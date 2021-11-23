from __future__ import print_function

import os.path
import urllib.request
import cv2
import numpy as np

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def getGoogleSheetData():
    print("Retrieving Photo Links from Google Sheet...")
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SPREADSHEET_ID = '18U8XIudQFbWEuH7s7tBzCYGv_qYhz4ysrm2fk_35RuQ'
    RANGE_NAME = 'Links!A1:A1000'
    creds = None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])
    links = set()

    if not values:
        print('No data found.')
    else:
        print(f"Accessed {len(values)} photos from Google Sheets")
        for i, row in enumerate(values):
            if i != 0:
                links.add(row[0])
    return list(links)

def download_images(links):
    success = 0
    for i, link in enumerate(links):
        try:
            urllib.request.urlretrieve(link, f"./images/raw/image{i}.jpg")
            success +=1
        except:
            print(f"Failed to download {link}")
    return success

def filter_image(imagePath):
    # Convert image
    img = cv2.imread(imagePath)

    # Create Edge Mask
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 7)

    # Transform the image
    data = np.float32(img).reshape((-1, 3))

    # Determine criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)

    # Implementing K-Means
    ret, label, center = cv2.kmeans(data, 9, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    result = center[label.flatten()]
    result = result.reshape(img.shape)

    # bilateral filter
    blurred = cv2.bilateralFilter(result, d=7, sigmaColor=200, sigmaSpace=200)

    cartoon = cv2.bitwise_and(blurred, blurred, mask=edges)

    return cartoon

def resize_image(image):
    dim = (631, 631)
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    
    return resized

def save_image(name, image):
    cv2.imwrite(f"./images/converted/{name}.jpg", image)

def border_image(image):
    image = cv2.copyMakeBorder(image, 100, 100, 50, 50, cv2.BORDER_REFLECT)
    BLACK = [0,0,0]
    image = cv2.copyMakeBorder(image, 40,40,40,40, cv2.BORDER_CONSTANT, value=BLACK)

    return image

def main():
    links = getGoogleSheetData()
    successful_downloads = download_images(links)

    for i in range(successful_downloads):
        photo_name = f"image{i}"
        print(f"Converting image {photo_name}")
        try:
            img = filter_image(f"./images/raw/{photo_name}.jpg")
            img = resize_image(img)
            img = border_image(img)
            print(f"Saving image {photo_name}")
            save_image(photo_name, img)
        except:
            print(f"Error converting {photo_name}.")

    # Custom photos
    extra_photos = ["test"]
    for photo_name in extra_photos:
        print(f"Converting image {photo_name}")
        try:
            # img = cv2.imread(f"./images/raw/{photo_name}.jpg")
            img = filter_image(f"./images/raw/{photo_name}.jpg")
            img = resize_image(img)
            img = border_image(img)

            print(f"Saving image {photo_name}")
            save_image(photo_name, img)
        except Exception as e:
            print(e)
            print(f"Error converting {photo_name}.")


if __name__ == '__main__':
    main()