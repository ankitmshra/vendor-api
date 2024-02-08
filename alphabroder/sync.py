import os
from datetime import datetime
from ftplib import FTP_TLS
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


class Process_alp_inventory():
    _skip_existing = True

    # AB connection info
    ftp_host = 'ftp.appareldownload.com'
    ftp_user = settings.AB_FTP_USER
    ftp_password = settings.AB_FTP_PASSWORD

    # AB Product files
    product_file = 'AllDBInfoALP_Prod.txt'
    inventory_file = 'inventory-v5-alp.txt'
    price_file = 'AllDBInfoALP_PRC_RZ99.txt'

    # image url
    image_url = 'https://www.alphabroder.com/media/hires/'

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
        download_to = os.path.join('files', 'alpb', filename)
        self.debug("Downloading '{}' to: {}".format(filename, download_to))

        local_file = open(download_to, 'wb')
        ftp.retrbinary(f'RETR {dir}{filename}', local_file.write)
        local_file.close()

    def download_alpha(self, filename):
        """Download the given file."""
        host = self.ftp_host
        user = self.ftp_user
        passwd = self.ftp_password

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.set_ciphers("DEFAULT")

        ftp = FTP_TLS(host=host, context=ssl_context, timeout=10)
        ftp.set_debuglevel(2)
        ftp.set_pasv(True)

        ftp.login(user=user, passwd=passwd)
        ftp.prot_p()  # Explicit FTP over TLS

        self.ensure_directory('files/alpb')  # Ensure 'files' directory exists
        self.download_file(ftp, filename)

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
        self.download_alpha(self.product_file)

    def prepare_inventory(self):
        """Prepare for updating product inventory by downloading relevant
          files."""
        self.download_alpha(self.inventory_file)

    def prepare_pricing(self):
        """Prepare for updating product pricing by downloading relevant
          files."""
        self.download_alpha(self.price_file)

    #####################################################
    #                   Update Products                 #
    #####################################################
    def update_products(self, filename):
        """Read product details from the text file and
          save them to the model."""
        file_path = os.path.join('files', 'alpb', filename)

        if not os.path.isfile(file_path):
            self.debug(f"File {filename} not found.")
            return

        self.debug(f"Updating products from file: {filename}")

        # Read the file using pandas
        df = pd.read_csv(file_path, sep='^', encoding='ISO-8859-1', error_bad_lines=False)

        # Iterate over rows and save to the model
        for _, row in df.iterrows():
            try:
                category, created = Category.objects.get_or_create(category=row['Category'])

                # Create or get Style
                product, created = Products.objects.get_or_create(
                    product_number=row['Style'],
                    defaults={
                        'short_description': row['Short Description'],
                        'brand_name': row['Mill Name'],
                        'category': category,
                        'full_feature_description': row['Full Feature Description'],
                    }
                )

                # Create Product
                variation_details = {
                    'item_number': row['Item Number'],
                    'product_number': product,
                    'color_name': row['Color Name'],
                    'color_code': row['Color Code'],
                    'hex_code': row['Hex Code'],
                    'size_code': row['Size Code'],
                    'size': row['Size'],
                    'case_qty': row['Case Qty'],
                    'weight': row['Weight'],
                    'front_image': row['Front Image Hi Res URL'].replace(self.image_url, ''),
                    'back_image': row['Back Image Hi Res URL'].replace(self.image_url, ''),
                    'side_image': row['Side Image Hi Res URL'].replace(self.image_url, ''),
                    'gtin': row['Gtin'],
                }
                # Use get_or_create for Products
                variation, created = Variations.objects.get_or_create(item_number=row['Item Number'], defaults=variation_details)

                if not created and not self._skip_existing:
                    Variations.objects.filter(item_number=row['Item Number']).update(**variation_details)
                    self.debug(f"Updated existing product with Item Number: {row['Item Number']}")
                elif not created:
                    self.debug(f"Skipped existing product with Item Number: {row['Item Number']}")
                else:
                    self.debug(f"Created new product with Item Number: {row['Item Number']}")

            except Exception as e:
                self.debug(f"Error processing row: {row}")
                self.debug(f"Error details: {e}")

                
    #####################################################
    #                  Update Inventory                 #
    #####################################################
    def update_inventory(self, filename):
        file_path = os.path.join('files', 'alpb', filename)

        if not os.path.isfile(file_path):
            self.debug(f"File {filename} not found.")
            return

        self.debug(f"Updating inventory from file: {filename}")

        # Read the file using pandas
        df = pd.read_csv(file_path, delimiter=',', encoding='ISO-8859-1', error_bad_lines=False)

        for _, row in df.iterrows():
            # check if the item number and gtin number are not empty. and same
            item_number = row['Item Number']
            gtin_number = row['GTIN Number']

            # Check if the item number is in the product list
            try:
                variation = Variations.objects.get(item_number=item_number, gtin=gtin_number)
            except Variations.DoesNotExist:
                self.debug(f"Product not found for Item Number: {item_number} and GTIN Number: {gtin_number}")
                continue  # Skip to the next iteration if the product doesn't exist

            quantity_sum = sum(
                int(row.get(field, 0)) for field in ['CC', 'CN', 'FO', 'GD', 'KC', 'MA', 'PH', 'TD', 'PZ', 'BZ', 'FZ', 'PX', 'FX', 'BX', 'GX']
            )

            variation.quantity = quantity_sum
            variation.save()

            self.debug(f"Updated inventory details for Item Number: {item_number} and GTIN Number: {gtin_number}")

    #####################################################
    #                   Update Pricing                  #
    #####################################################
    def update_pricing(self, filename):
        file_path = os.path.join('files', 'alpb', filename)

        if not os.path.isfile(file_path):
            self.debug(f"File {filename} not found.")
            return

        self.debug(f"Updating Pricing from file: {filename}")

        # Read the file using pandas
        df = pd.read_csv(file_path, sep='^', encoding='ISO-8859-1', error_bad_lines=False)

        # Iterate over rows and save to the model
        for _, row in df.iterrows():
            # check if the item number and gtin number are not empty. and same
            item_number = row['Item Number ']
            gtin_number = row['Gtin']

            # Check if the item number is in the product list
            try:
                variation = Variations.objects.get(item_number=item_number, gtin=gtin_number)
            except Variations.DoesNotExist:
                self.debug(f"Product not found for Item Number: {item_number} and GTIN Number: {gtin_number}")
                continue  # Skip to the next iteration if the product doesn't exist

            def clean_numeric(value):
                if pd.isna(value) or value == '“nan”':
                    return None
                numeric_value = ''.join(char for char in str(value) if char.isdigit() or char == '.')
                # Convert the cleaned numeric value to a Decimal
                return Decimal(numeric_value) if numeric_value else None

            # Update the product details
            variation.price_per_piece = clean_numeric(row['Piece'])
            variation.price_per_dozen = clean_numeric(row['Dozen'])
            variation.price_per_case = clean_numeric(row['Case'])
            variation.retail_price = clean_numeric(row['Retail'])
            variation.save()
            self.debug(f"Updated Pricing details for Item Number: {item_number} and GTIN Number: {gtin_number}")
                             
                
    #####################################################
    #                   Update Handler                  #
    #####################################################
    def handle(self):
        """Handle GET requests to start downloading, processing,
          and updating the model."""
        self.clean_directory(os.path.join('files', 'alpb'))
        self.prepare_products()
        self.update_products(self.product_file)
        self.prepare_inventory()
        self.update_inventory(self.inventory_file)
        self.prepare_pricing()
        self.update_pricing(self.price_file)
        self.debug("Finished updating products and inventory and Pricing.")
        return True

class UpdateALPDB():
    def start(self):
        try:
            process_alp_inventory = Process_alp_inventory()
            resp = process_alp_inventory.handle()
            return HttpResponse("Data updated successfully.")

        except Exception as e:
            return HttpResponseServerError(f"Error during update: {str(e)}")