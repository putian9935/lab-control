import pyautogui
screen_size = pyautogui.size()
import time


defaultLocation = {
    'camStartAcqIcon':[154,78],
    'camSettingIcon':[266,78],
    'camSettingFilenameEntryBox':[803,399],
    'nowhere':[903,699],
    'camSettingSpoolingTab':[935,210],
    'camSettingOkBtn':[1034,831],
    'camStopAcqIcon':[241,74]
    }

    
def action_changeFilenameAndStartCamAcq(filename='exp00'):
    # bring window to foreground
    win_handle = pyautogui.getWindowsWithTitle('Andor SOLIS')[0]
    win_handle.restore()
    win_handle.maximize()
    time.sleep(0.05)
    pyautogui.click(*defaultLocation['camSettingIcon'], clicks=1)
    time.sleep(0.05)
    pyautogui.click(*defaultLocation['camSettingSpoolingTab'])
    time.sleep(0.05)
    pyautogui.click(*defaultLocation['camSettingFilenameEntryBox'])
    with pyautogui.hold('ctrl'):
            pyautogui.press(['A'])
    pyautogui.write(filename, interval=1e-2)
    pyautogui.click(*defaultLocation['camSettingOkBtn'])
    time.sleep(0.5)
    pyautogui.click(*defaultLocation['camStartAcqIcon'])
    pyautogui.moveTo(*defaultLocation['nowhere'])

def action_StopCamAcq(filename='exp00'):
    # bring window to foreground
    win_handle = pyautogui.getWindowsWithTitle('Andor SOLIS')[0]
    win_handle.restore()
    win_handle.maximize()
    time.sleep(0.05)
    pyautogui.click(*defaultLocation['camStopAcqIcon'], clicks=1)
    time.sleep(2)

if __name__ == "__main__":
    input('hit enter to start?')
    filename='exp1_{}'.format(round(time.time()))
    action_changeFilenameAndStartCamAcq(filename)
