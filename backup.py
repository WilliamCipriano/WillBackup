import os
import time
import shutil

Source = ""
Destination = ""
KeepMinutes = 0

state = "UP"

try:
    path = os.path.dirname(os.path.abspath(__file__))
except NameError:  # We are the main py2exe script, not a module
    import sys
    path = os.path.dirname(os.path.abspath(sys.argv[0]))

def loadconfig():
    global Source
    global Destination
    global KeepMinutes

    try:
        config = open(path + '/backupconfig.ini')
        config = config.read().split('=')
        csource = config[1].split('\n')[0]
        csource = csource[1:]
        cdestination = config[2].split('\n')[0]
        cdestination = cdestination[1:]
        ckeepminutes = config[3].split('\n')[0]
        ckeepminutes = ckeepminutes[1:]

        Source = csource
        Destination = cdestination
        KeepMinutes = int(ckeepminutes)

    except Exception as ex:
        DefaultLoggingFunction(text="Failed to load config file!", code=4)

def DefaultLoggingFunction(error = True, critical=True, text="Undefined Error Encountered!", code = False):
    global path
    global state
    try:
        if not os.path.exists(path + '/logs/'):
            os.makedirs(path + '/logs/')
    except Exception as ex:
        print ex
        state = "Logging: Bad Path"
        return False

    try:
        log = open(path + '/logs/error.log', 'a')
        message = ''
        if error:
            if critical:
                if state != "UP":
                    message += '   !!'
                else:
                    message += '    !'
            else:
                if state != "UP":
                    message += '   @@'
                else:
                    message += '    @'
        else:
            message += '    *'
        message += ": " + text
        if code:
            message += " {" + str(code) + "} \n"
        else:
            message += " {0} \n"
        try:
            log.write(message)
        except Exception as ex:
            state = "Logging: Bad File"
            print ex
            return False

    except Exception as ex:
        state = "Logging: Global Failure"
        print ex
        return False
    if state != "UP" and state != "CLEAR":
        status = state
        state = "CLEAR"
        DefaultLoggingFunction(text="Error State:'" + status + "' Reset.", code=999)


def getOldDirs(dirPath, olderThanMinutes):
    try:
        olderThanMinutes *= 60
        present = time.time()
        directories = []
        for root, dirs, files in os.walk(dirPath, topdown=False):
            for name in dirs:
                subDirPath = os.path.join(root, name)
                if (present - os.path.getmtime(subDirPath)) > olderThanMinutes:
                    directories.append(subDirPath)
        return directories
    except Exception as ex:
        DefaultLoggingFunction(critical=False, text="Old backup crawl failure. <" + ex + ">", code=2)
        global state
        state = "Error 2: Old backup crawl failure."
        return False


def delete(directories):
    try:
        for locale in directories:
            shutil.rmtree(locale)
            DefaultLoggingFunction(error = False, text=locale + " was removed due to age", code=1)
        return True
    except Exception as ex:
        DefaultLoggingFunction(critical=False, text=locale + " deletion failed. <" + ex + ">", code=3)
        global state
        state = "Error 3: Old backup delete failure."
        return False

def autodelete(location, minutes=43200):
    directories = getOldDirs(location, minutes)
    success = False
    if directories:
        success = delete(directories)
    if success:
        return True
    else:
        return False

def backup(src, dest):
    try:
        dest = dest + "/BACKUP " + time.strftime('%b-%d--%H-%M') + "/"
        os.makedirs(dest)
        src_files = os.listdir(src)
        for file_name in src_files:
            DefaultLoggingFunction(error=False, critical=False ,text='Wrote ' + file_name, code=5)
            full_file_name = os.path.join(src, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, dest)
        return True
    except Exception as Ex:
        DefaultLoggingFunction(text='WARNING: Backup Failure! <' + str(Ex) + '>', code=6)
        global state
        state = "DOWN"
        return False



loadconfig()
autodelete(Destination, KeepMinutes)
if backup(Source, Destination):
    print "Backup Complete!"
    time.sleep(3)
else:
    print "Backup Failure! Please alert the system administrator and view the log located at logs\error.log (This may be from running the backup twice in one minute)"
    time.sleep(3599)
