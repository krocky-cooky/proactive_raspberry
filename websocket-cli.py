import websocket
import traceback    # 例外時のスタックとレースを表示するモジュール。
import json
import pprint
import serial 
import time 
import threading 


class EmotionHandler(object):
    def __init__(
        self,
        url,
        port = None
    ):
        self.candidate_emotion = dict()
        self.url = url
        #self.serial = serial.Serial(port,9600)
    
    def start(self):
        ws = websocket.WebSocketApp(self.url,
                                on_open=self.on_open,
                                on_message=self.on_message,
                                on_error=self.on_error,
                                on_close=self.on_close,
                                on_cont_message=self.on_cont_message,
                                on_data=self.on_data)
                        
        t = threading.Thread(target = self.set_interval_worker,daemon=True)
        t.start()
        ws.run_forever()
    
    def get_normalized_expression(self,obj):
        expressions = ["angry","disgusted","fearful","happy","sad","surprised"]
        pos = 0
        neg = 0
        for exp in expressions:
            pos += obj["expressions"][exp]
        neg += obj["expressions"]["neutral"]
        add = pos + neg
        if add  <= 0.0:
            return 0 
        pos /= add 
        neg /= add 
        output = pos-neg
        return output 

    def get_normalized_sound(self,obj):
        sound = obj["sound"]
        if sound is None:
            return False
        return sound > 100
    
    def on_open(self,ws):
        """WebSocketを開いた時の関数。"""
        print("###open###")
        ws.send("{\"action\": \"cliamMaster\"}")


    def on_message(self,ws, message):
        """
        データを受信したときの関数。
        
        Parameters
        --------
        ws:         WebSocketのクラスオブジェクト。
        message:    受信したデータ(utf-8)。
        """
        if "disconnected" in message:
            connectionId = message.split()[0]
            if connectionId in self.candidate_emotion.keys():
                del self.candidate_emotion[connectionId]
            return 
        received_data = json.loads(message)
        connectionId = received_data["connectionId"]
        if connectionId not in self.candidate_emotion.keys():
            self.candidate_emotion[connectionId] = dict({"expression":None,"sound" : None,"candidateId": None})
        
        self.candidate_emotion[received_data["connectionId"]]["expression"] = self.get_normalized_expression(received_data)
        self.candidate_emotion[received_data["connectionId"]]["sound"] = self.get_normalized_sound(received_data)
        self.candidate_emotion[received_data["connectionId"]]["candidateId"] = received_data["candidateId"]
        # pprint.pprint(self.candidate_emotion)
        # print(received_data["connectionId"], " send data")

    def on_error(self,ws, error):
        """
        エラーを受信したときの関数。
        
        Parameters
        --------
        ws:     WebSocketのクラスオブジェクト。
        error:  例外オブジェクト。
        """
        print("###on_error###")
        # print("error: %s" % error)
        print(traceback.format_exc())

        ws.close()

    def on_close(self,ws, close_status_code, close_msg):
        """
        接続を終了するときの関数。
        
        Parameters
        --------
        ws:                 WebSocketのクラスオブジェクト。
        close_status_code:  終了時ステータスコード。
        close_msg:          終了時メッセージ。
        """
        print("###close###")
        print("status: %d" % close_status_code)
        print("message: " + close_msg)

    def on_cont_message(self,ws, message, continue_flag):
        """
        
        
        Parameters
        --------
        ws:             WebSocketのクラスオブジェクト。
        message:        取得したメッセージ(utf-8)。
        continue_flag:  続行フラグ。
        """
        print("###on_cont_message###")
        print("message: " + message)
        print("flag: %s" % continue_flag)

    def on_data(self,ws, data, data_type, continue_flag):
        """
        データを受信したときの関数。バイナリにも対応できる。
        
        Parameters
        --------
        ws:             WebSocketのクラスオブジェクト。
        data:           取得したメッセージ(utf-8)。
        data_type:      データ型（テキストかバイナリか）。
        continue_flag:  続行フラグ。
        """
        # print("###on_data###")
        # print("data: %s" % data)
        # print("data_type: %s" % data_type)
        # print("continue_flag: %s" % continue_flag)

    def set_interval_worker(self):
        while True:
            serial_json = dict()
            for val in self.candidate_emotion.values():
                serial_json["candidate" + str(val["candidateId"])] = {"expression": val["expression"], "sound": val["sound"]}
            pprint.pprint(serial_json)
            
            serial_json = json.dumps(serial_json)
            #self.serial.write((serial_json+'\r\n').encode('utf-8'))
            time.sleep(1)

    




if __name__ == "__main__":
    url = "wss://nw66veb21f.execute-api.ap-northeast-1.amazonaws.com/production"
    handler = EmotionHandler(url = url,port = "COM12")
    handler.start()

    
