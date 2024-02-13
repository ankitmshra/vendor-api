import os
from datetime import datetime
from ftplib import FTP
import ssl
import shutil
from decimal import Decimal
import logging

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseServerError

import pandas as pd


# import product models
from .models import Category, Products, Variations


class Process_snmr_inventory():
    _skip_existing = False

    # AB connection info
    ftp_host = 'ftp.sanmar.com'
    ftp_user = settings.SANMAR_FTP_USER
    ftp_password = settings.SANMAR_FTP_PASSWORD

    # AB Product files
    product_csv = 'SanMar_EPDD.csv'    

    def __init__(self, download=True, debug=True, suffix=None,
                 basename=None, detail=None):
        """Initialize inventory by parsing provided inventory
          CSV file and building a dict of all inventory items."""
        self._db = None
        self._download = download
        self._debug = debug
        self._suffix = suffix
        self._basename = basename
        self._detail = detail
        self._current_products = {}
        self._product_images = {}
        self.logger = logging.getLogger(__name__)

    #####################################################
    #                       Commons                     #
    #####################################################
        
    def ensure_directory(self, directory):
        """Ensure that the given directory exists."""
        if not os.path.exists(directory):
            os.makedirs(directory)

    def download_file(self, ftp, filename, dir=''):
        """Download given file from global FTP server."""
        download_to = os.path.join('files', 'snmr', filename)
        self.debug("Downloading '{}' to: {}".format(filename, download_to))

        local_file = open(download_to, 'wb')
        ftp.retrbinary(f'RETR {dir}{filename}', local_file.write)
        local_file.close()

    def download_snmr(self, filename):
        """Download the given file."""
        host = self.ftp_host
        user = self.ftp_user
        passwd = self.ftp_password

        ftp = FTP(host=host, timeout=10)
        ftp.set_debuglevel(2)

        ftp.login(user=user, passwd=passwd)

        self.ensure_directory('files/snmr')  # Ensure 'files' directory exists
        self.download_file(ftp, filename, dir='SanMarPDD/')

        ftp.quit()
        
    def clean_directory(self, directory):
        """Clean the given directory by removing all files."""
        self.debug(f"Cleaning directory: {directory}")
        try:
            shutil.rmtree(directory)
            os.makedirs(directory)
            self.debug(f"Directory cleaned successfully.")
        except Exception as e:
            self.debug(f"Error cleaning directory: {e}")
    
    def debug(self, msg, force=False):
        """Method for printing debug messages."""
        if self._debug or force:
            print("<{}>: {}".
                  format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))

            
    #####################################################
    #     Download Inventory, products, Price file      #
    #####################################################
        
    def prepare_products(self):
        """Prepare for updating products by downloading relevant files."""
        self.download_snmr(self.product_csv)

    #####################################################
    #                   Update Products                 #
    #####################################################
    def update_products(self, filename):
        """Read product details from the text file and
          save them to the model."""
        file_path = os.path.join('files', 'snmr', filename)

        if not os.path.isfile(file_path):
            self.debug(f"File {filename} not found.")
            return

        self.debug(f"Updating products from file: {filename}")

        # Read the file using pandas
        df = pd.read_csv(file_path, sep=',', encoding='ISO-8859-1', error_bad_lines=False)

        # Iterate over rows and save to the model
        for _, row in df.iterrows():
            try:
                if(row['PRODUCT_STATUS'] != 'Discontinued'):
                    category, created = Category.objects.get_or_create(category=row['CATEGORY_NAME'])

                    # Create or get Style
                    product, created = Products.objects.get_or_create(
                        product_number=row['THUMBNAIL_IMAGE'].split('.')[0],
                        defaults={
                            'short_description': row['PRODUCT_TITLE'],
                            'brand_name': row['MILL'],
                            'category': category,
                            'full_feature_description': row['PRODUCT_DESCRIPTION'],
                        }
                    )

                    # Create Product
                    front_img_url = None
                    back_img_url = None
                    if not pd.isna(row['FRONT_MODEL_IMAGE_URL']):
                        front_img_url = row['FRONT_MODEL_IMAGE_URL']
                        base_url = front_img_url.rsplit('/', 1)[0]
                        if not pd.isna(row['BACK_MODEL_IMAGE']):
                            back_img_url = base_url + '/' + row['BACK_MODEL_IMAGE']

                    variation_details = {
                        'item_number': row['UNIQUE_KEY'],
                        'product_number': product,
                        'color_name': row['COLOR_NAME'],
                        'hex_code': row['COLOR_SQUARE_IMAGE'],
                        'size': row['SIZE'],
                        'case_qty': row['CASE_SIZE'],
                        'weight': row['PIECE_WEIGHT'],
                        'front_image': front_img_url,
                        'back_image': back_img_url,
                        'gtin': str(row['GTIN']),
                    }
                    # Use get_or_create for Products
                    variation, created = Variations.objects.get_or_create(item_number=row['UNIQUE_KEY'], defaults=variation_details)

                    if not created and not self._skip_existing:
                        Variations.objects.filter(item_number=row['UNIQUE_KEY']).update(**variation_details)
                        self.debug(f"Updated existing product with Item Number: {row['UNIQUE_KEY']}")
                    elif not created:
                        self.debug(f"Skipped existing product with Item Number: {row['UNIQUE_KEY']}")
                    else:
                        self.debug(f"Created new product with Item Number: {row['UNIQUE_KEY']}")
                else:
                    self.debug(f"Skipped existing product with Item Number: {row['UNIQUE_KEY']} as product is Discontinued.")

            except Exception as e:
                self.debug(f"Error processing row: {row}")
                self.debug(f"Error details: {e}")

                
    #####################################################
    #                  Update Inventory                 #
    #####################################################
    def update_inventory(self, filename):
        file_path = os.path.join('files', 'snmr', filename)

        if not os.path.isfile(file_path):
            self.debug(f"File {filename} not found.")
            return

        self.debug(f"Updating inventory from file: {filename}")

        # Read the file using pandas
        df = pd.read_csv(file_path, delimiter=',', encoding='ISO-8859-1', error_bad_lines=False)

        for _, row in df.iterrows():
            # check if the item number and gtin number are not empty. and same
            item_number = row['UNIQUE_KEY']
            gtin_number = str(row['GTIN'])

            # Check if the item number is in the product list
            try:
                variation = Variations.objects.get(item_number=item_number, gtin=gtin_number)
            except Variations.DoesNotExist:
                self.debug(f"Product not found for Item Number: {item_number} and GTIN Number: {gtin_number}")
                continue  # Skip to the next iteration if the product doesn't exist

            variation.quantity = row['QTY']
            # update pricing
            def clean_numeric(value):
                if pd.isna(value) or value == '“nan”':
                    return None
                numeric_value = ''.join(char for char in str(value) if char.isdigit() or char == '.')
                # Convert the cleaned numeric value to a Decimal
                return Decimal(numeric_value) if numeric_value else None

            # Update the product details
            variation.price_per_piece = clean_numeric(row['PIECE_PRICE'])
            variation.price_per_dozen = clean_numeric(row['DOZENS_PRICE'])
            variation.price_per_case = clean_numeric(row['CASE_PRICE'])
            variation.retail_price = clean_numeric(row['MSRP'])
            variation.save()

            self.debug(f"Updated inventory and Pricing details for Item Number: {item_number} and GTIN Number: {gtin_number}")
                
    #####################################################
    #                   Update Handler                  #
    #####################################################
    def handle(self):
        """Handle GET requests to start downloading, processing,
          and updating the model."""
        self.clean_directory(os.path.join('files', 'snmr'))
        self.prepare_products()
        self.update_products(self.product_csv)
        self.update_inventory(self.product_csv)
        self.debug("Finished updating products and inventory and Pricing.")
        return True

class UpdateSNMRDB():
    def start(self):
        try:
            process_snmr_inventory = Process_snmr_inventory()
            resp = process_snmr_inventory.handle()
            return HttpResponse("Data updated successfully.")

        except Exception as e:
            return HttpResponseServerError(f"Error during update: {str(e)}")