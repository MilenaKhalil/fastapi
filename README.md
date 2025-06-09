
# Fastapi
Web app using fastAPI where you can create users, authenticate, add books to a cathalog (if you are an admin) and see all the books you've added (if you are logged in). The program is using sqlite database on your computer

## How to run the project

First download the repo and enter it:

```console
git clone https://github.com/MilenaKhalil/fastapi my_project
cd my_project
```

Install required libs:

```console
./install.sh
```

After the installation run the following:

```console
source ./venv/bin/activate
uvicorn main:app --reload --port 8001
```
> If you want to use a default port don't add `--port 8001` it will be on the 8000 port by default. (or you can choose a different port if you want).

If you don't have any errors run this on your browser:

```console
http://localhost:8001/docs
```

> If you have a different port write it instead of 8001

### How to view the database?

I am using a VSCode extention called SQLite Viewer. If you install it and open the data.db file you will be able to see the database of users and books

### Starting and restarting the project

In order to stop the unicorn you should press `CTRL-C` otherwise you will continue to have this prosses on 8001 port and you will get this error after reloading

```console
ERROR:    [Errno 98] Address already in use
```

So if you want to solve it, first get PID of the prosess:

```console
sudo lsof -i :8001
```

Then run:

```console
sudo kill -9 <PID>
```
