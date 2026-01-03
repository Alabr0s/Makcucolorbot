import urllib.request
import json
import os
import ssl
import shutil

def test_download():
    # Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, 'image')
    cache_dir = os.path.join(img_dir, 'cache')
    
    if not os.path.exists(cache_dir):
        print(f"Creating directory: {cache_dir}")
        os.makedirs(cache_dir, exist_ok=True)

    print(f"Target Directory: {cache_dir}")

    # SSL Context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://valorant-api.com/v1/weapons"
    print(f"Requesting {url}...")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as r:
            data = json.loads(r.read().decode())
            
        print(f"API Success. Found {len(data['data'])} weapons.")
        
        # Try downloading one
        item = data['data'][0]
        name = item['displayName']
        icon_url = item['displayIcon']
        print(f"Attempting to download {name} from {icon_url}")
        
        save_path = os.path.join(cache_dir, "test_download.png")
        
        img_req = urllib.request.Request(icon_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(img_req, context=ctx) as ir:
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(ir, f)
                
        print(f"Success! Saved to {save_path}")
        print(f"File size: {os.path.getsize(save_path)} bytes")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_download()
