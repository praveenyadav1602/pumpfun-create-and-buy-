import os
import requests

API_URL = "https://pump.fun/api/ipfs"

def create_token_metadata(name, symbol, description, image_path, twitter="", telegram="", website=""):
    try:
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")
        with open(image_path, "rb") as f:
            image_data = f.read()

        files = {
            "file": (os.path.basename(image_path), image_data, "image/png"),
            **{k: (None, v) for k, v in {
                "name": name,
                "symbol": symbol,
                "description": description,
                "twitter": twitter,
                "telegram": telegram,
                "website": website,
                "showName": "true"
            }.items()}
        }

        r = requests.post(API_URL, files=files)
        if not r.ok:
            raise Exception(f"HTTP {r.status_code}: {r.text}")
        j = r.json()
        uri = j.get("metadataUri")
        print(uri)
        return uri
    except Exception as e:
        print(f"Error: {e}")
        return None

# Metadata input and creation logic
name = "World War"
symbol = "WW3"
description = "Kim Jong Un attacked the QuickNode and Helius offices."
image = "./www.png"
twitter = "https://x.com/x_worldwar3"
telegram = "https://t.me/ww3_kim"
website = "https://twitter.com/i/communities/1935587182216966593?t=0uDLmtUzBXG4tkalGxNLkg&s=09"

# This variable will be available to import
metadaturi = create_token_metadata(name, symbol, description, image, twitter=twitter, telegram=telegram, website=website)
