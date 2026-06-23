import os
import sys
import re
import subprocess
import urllib.request
import urllib.error
import json

# تنظیم انکودینگ خروجی کنسول روی UTF-8 جهت جلوگیری از خطای یونیکد در ویندوز
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def load_env(env_path):
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    match = re.match(r"^\s*([\w.-]+)\s*=\s*(.*)\s*$", line)
                    if match:
                        key = match.group(1)
                        val = match.group(2).strip()
                        # Remove quotes if present
                        if val.startswith(('"', "'")) and val.endswith(('"', "'")):
                            val = val[1:-1]
                        env_vars[key] = val
    return env_vars

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_dir, ".env")
    
    # 1. خواندن مقادیر فایل .env
    env = load_env(env_path)
    token = env.get("GITHUB_TOKEN", "")
    username = env.get("GITHUB_USERNAME", "")
    
    if not token or token == "your_github_token_here":
        print("[ERROR] خطا: لطفاً ابتدا توکن گیت‌هاب (Personal Access Token) خود را در فایل .env قرار دهید.")
        print("مقدار فعلی GITHUB_TOKEN نامعتبر یا پیش‌فرض است.")
        return

    repo_name = "RTL-view"
    print(f"Creating public repository '{repo_name}' on GitHub...")
    
    # 2. فراخوانی API گیت‌هاب برای ساخت مخزن پابلیک
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    data = {
        "name": repo_name,
        "private": False, # ساخت مخزن به صورت Public
        "description": "A Windows popup utility to view selected text in right-to-left (RTL) format with custom font and syntax highlighting."
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    clone_url = ""
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            html_url = res_data.get("html_url", "")
            clone_url = res_data.get("clone_url", "")
            print(f"[OK] مخزن با موفقیت در گیت‌هاب ساخته شد: {html_url}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        # بررسی اینکه آیا مخزن قبلاً ساخته شده است یا خیر
        if e.code == 422 and "already exists" in err_msg:
            print(f"[INFO] مخزن '{repo_name}' از قبل در اکانت شما وجود دارد.")
            # حدس زدن کلون URL در صورت وجود نام کاربری
            if username and username != "your_username_here":
                clone_url = f"https://github.com/{username}/{repo_name}.git"
            else:
                print("[ERROR] خطا: مخزن از قبل وجود دارد اما GITHUB_USERNAME در فایل .env ست نشده است تا پروژه را به آن لینک کنیم.")
                return
        else:
            print(f"[ERROR] خطا در ساخت مخزن گیت‌هاب: Code {e.code}")
            print(err_msg)
            return
    except Exception as e:
        print(f"[ERROR] خطای غیرمنتظره در ارتباط با گیت‌هاب: {e}")
        return

    if not clone_url:
        print("[ERROR] خطای غیرمنتظره: آدرس کلون مخزن یافت نشد.")
        return

    # 3. پیکربندی محلی گیت و ارسال کدها (Push)
    try:
        # تغییر نام برنچ به main
        subprocess.run(["git", "branch", "-M", "main"], cwd=project_dir, check=True)
        
        # بررسی اینکه آیا ریموت origin از قبل وجود دارد
        remotes = subprocess.run(["git", "remote"], cwd=project_dir, capture_output=True, text=True).stdout
        if "origin" in remotes:
            subprocess.run(["git", "remote", "remove", "origin"], cwd=project_dir, check=True)
            
        # اضافه کردن ریموت جدید با استفاده از توکن برای لاگین خودکار
        auth_clone_url = clone_url.replace("https://", f"https://{token}@")
        subprocess.run(["git", "remote", "add", "origin", auth_clone_url], cwd=project_dir, check=True)
        
        print("Pushing files to GitHub (main branch)...")
        # پوش کردن کدها به گیت‌هاب
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=project_dir, check=True)
        print("[SUCCESS] پروژه با موفقیت به گیت‌هاب ارسال شد!")
        
        # برای امنیت بیشتر، آدرس ریموت حاوی توکن را به آدرس عمومی تغییر می‌دهیم تا توکن در پروژه ذخیره نشود
        subprocess.run(["git", "remote", "set-url", "origin", clone_url], cwd=project_dir, check=True)
        print("[SECURE] امنیت ریموت گیت تامین شد (توکن از کانفیگ محلی حذف گردید).")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] خطا در اجرای دستورات گیت: {e}")
    except Exception as e:
        print(f"[ERROR] خطای غیرمنتظره در گیت: {e}")

if __name__ == "__main__":
    main()
