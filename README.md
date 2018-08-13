# 課後社團報名系統 (afc-github)
國小階段課後社團報名系統，提供學生家長線上報名使用。管理者可自行匯入「學生」與「課程」資料，進行編輯與管理；學生家長可線上進行「選課」。

實際運作畫面 https://afc.chps.tn.edu.tw/

## 1. 系統資訊
  - GNU/Linux，如 CentOS、Fedora、Debian 等
  - SQLite3
```bash
# sudo dnf install sqlite
OR
# sudo apt-get install sqlite
```
  - Python Babel
```bash
# sudo dnf install babel
OR
# sudo apt-get install python-pybabel
```
  - Python 2.7 以上，及如下模組
```bash
# sudo dnf install python-pip
OR
# sudo apt-get install python-pip
```
```
alembic
Flask
Flask_Babel
Flask_Login
Flask_Migrate
Flask_Script
Flask_SQLAlchemy
Flask_WTF
pytz
SQLAlchemy
Werkzeug
WTForms
```


## 2. 程式安裝

### 下載原始碼
```bash
# git clone https://github.com/lyshie/afc-github
```

### 編輯設定檔
```bash
# cd afc-github/
# touch app/config.py
# vim config.py
# vim app/config.py
```
```
RECAPTCHA_PUBLIC_KEY = ""    # 沒有申請就不用填
RECAPTCHA_PRIVATE_KEY = ""   # 沒有申請就不用填
```

### 安裝 Python 相關模組
```bash
# pip install --upgrade --user -r requirements.txt
```

### 建立初始資料庫
```bash
# cd afc-github/
# sqlite3 app.db < afc.sql
```

### 建立管理者
```bash
# cd afc-github/
# vim app/scripts/db_create_admin.py
```
```
user.uid = 0                        # 'uid = 0' 是管理者
user.student_grade    = 6           # 管理者虛擬年級
user.student_class    = 6           # 管理者虛擬班級
user.student_number   = 99          # 管理者虛擬座號
user.student_name     = "admin"     # 管理者姓名
user.default_password = "PaSSwoRD"  # 管理者密碼
```
```bash
# ./app/scripts/db_create_admin.py
```

### 產生語系翻譯檔(中文正體)
```bash
# cd afc-github/
# ./tr_update.sh
```
pybabel 執行如有錯誤，建議先更新 setuptools。
```bash
# pip install --upgrade --user setuptools
```

### 測試執行
開啟瀏覽器，連結至 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)，嘗試以管理者帳號登入。
```bash
# cd afc-github/
# ./run.py
```
```
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
 * Restarting with inotify reloader
 * Debugger is active!
 * Debugger pin code: 316-959-504
```

### 編輯使用者
以 JSON 格式匯出使用者資料，透過文字編輯器進行修改。
```bash
# cd afc-github/
# ./app/scripts/db_user.py export -u 0 | json_reformat > /tmp/user
# vim /tmp/user
```
```
{
    "default_password": "PaSSwoRD",
    "parent_name": "管媽媽",
    "parent_phone": "06-2133007#812",
    "password": "",
    "student_class": 6,
    "student_grade": 6,
    "student_name": "管理者",
    "student_number": 99,
    "student_tag": "N",
    "uid": 0
}
```
修改存檔後，再度以 JSON 格式匯入，更新使用者資料。
```bash
# cat /tmp/user | ./app/scripts/db_user.py update
```

### 匯入使用者
僅附加使用者，可作為增加使用者。
```bash
# ./app/scripts/import_user.py import_user -f /tmp/user.csv
```
取代既有使用者資料，可作為更新使用。
```bash
# ./app/scripts/import_user.py import_user -f /tmp/user.csv -r
```

### 匯出課程
```bash
# cd afc-github/
# ./app/scripts/export_course.py export_course -f /tmp/courses.csv
```

### 匯入課程
僅附加課程，可作為增加課程。
```bash
# ./app/scripts/import_course.py import_course -f /tmp/course.csv
```
取代既有課程資料，可作為更新使用。
```bash
# ./app/scripts/import_course.py import_course -f /tmp/course.csv -r
```

### 新增選課測試資料
隨機產生選課測試資料，但仍符合選課條件限制。
```bash
./app/scripts/db_create_testdata.py
```

### 清除所有選課資料
```bash
# sqlite3 app.db < sql/empty_selection.sql
```

## 3. 系統封存與一致性檢查
匯出每一筆完整選課資料(合併 selections、course 與 user 資料表)，並紀錄所有選課人數與選課順序。
```bash
# sqlite3 app.db < sql/full_selections.sql
```

匯出每一筆有效的選課資料(達開課人數下限與正取資格者)，以供核對與收費統計。
```bash
# sqlite3 app.db < sql/valid_selection.sql
```

統計每個使用者的課程費用支出。
```bash
# sqlite3 app.db < ./sql/valid_selection_groupby_user.sql
```

統計「開課課程總數」、「總上課人次」、「總上課人數」與「總收費金額」等資訊。
```bash
# sqlite3 app.db < ./sql/valid_selection_total_cost.sql
```

各班級、各年級選課統計資訊。
```bash
# sqlite3 app.db < ./sql/valid_selection_groupby_gc.sql
```

## 4. 使用 docker 配置
使用 nginx-gunicorn-flask
```bash
# docker pull danriti/nginx-gunicorn-flask
# docker run -t -i danriti/nginx-gunicorn-flask /bin/bash
935b9549c94f:/# apt-get install git vim
935b9549c94f:/# cd /deploy
935b9549c94f:/# git clone https://github.com/lyshie/afc-github
935b9549c94f:/# cd /deploy/afc-github
935b9549c94f:/# pip install --upgrade --user -r requirements.txt 
935b9549c94f:/# vim /etc/supervisor/conf.d/gunicorn.conf
[program:gunicorn]
command=/usr/bin/gunicorn app:app -b localhost:5000
directory=/deploy/afc-github
935b9549c94f:/# exit
# docker commit -m "Added APP" -a "SHIE, Li-Yi" [BASE IMAGE ID]
# docker run -t -i -p 80:80 [NEW IMAGE ID] /bin/bash
```

使用 nginx-gunicorn-flask-afc
```bash
# docker pull lyshie/nginx-gunicorn-flask-afc
# docker run -d -p 80:80 lyshie/nginx-gunicorn-flask-afc
```

更新至最新版本
```bash
# docker run -t -p 80:80 lyshie/nginx-gunicorn-flask-afc /bin/bash
# cd /deploy/afc-github
# git pull
# exit
# docker commit --change='CMD ["/usr/bin/supervisord"]' -m "Update afc-github from GitHub" -a "Myself" [CONTAINER ID]
# docker run -d -p 80:80 [IMAGE ID]
```

## 5. 使用 virtualenv 配置
[部署在臺南市飛番雲 IaaS 平台](https://github.com/lyshie/afc-github/blob/master/tn_iaas.md)

## 6. 參考資訊
  - HSIEH, Li-Yi @ [臺南市進學國小資訊組](http://www.chps.tn.edu.tw/)
  - All programs are released under the GPL.
  - Free icons from [www.flaticon.com](http://www.flaticon.com/) is licensed by [CC 3.0 BY](http://creativecommons.org/licenses/by/3.0/)
