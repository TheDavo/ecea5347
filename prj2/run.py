import webbrowser
import server.server
import os

cwd = os.getcwd()
fp = "file://./client/prj2.html"
url = os.path.join("file://", cwd, "client/prj2.html")
webbrowser.open(url, new=2)  # open in new tab
server.server.main()
