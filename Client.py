from socket import *
import select
from random import random

class Data(object):
  """
    要发送的数据包
    msg为报文内容 字节序列
    type表示类型，0为数据报文，1为ack报文
    seq表示序列号
    state只在发送端使用，不发送到接收端 state为0表示待发送，为1表示已发送， 为2表示已发送且已收到ACK
  """
  def __init__(self,msg,type,seq = 0,state = 0) :
    self.message = msg
    self.type = str(type)
    self.seq = str(seq)
    self.state = state
  def __str__(self):
    return self.seq + self.type + self.message


class Client:
  def __init__(self) :
    self.nextseqnum = 1 #这里可以是0
    self.maxDelayTime = 5
    self.maxWaitTime = 10
    self.clientAddr = ('localhost',3400)
    self.serverAddr = ('localhost',3401)
    self.socket = socket(AF_INET, SOCK_DGRAM)
    self.sendWindow = []
    self.rev_data = ''
    self.pkgNum = 0
    self.sendWindowMax = 4

  def send(self,buffer):
    pkgTimer = 0 # 发送数据计时
    self.pkgNum = len(buffer) # 包的序列号
    last_ack = 0
    msg_timer = 0 # 收到数据计时

    #检查发送窗是否已满。没满加入一些data
    while len(self.sendWindow) < self.sendWindowMax:
      if(self.nextseqnum > self.pkgNum):
        break
      data = Data(buffer[self.nextseqnum - 1], 0, seq=self.nextseqnum)
      self.sendWindow.append(data)
      self.nextseqnum +=1

    #查看发送窗里的数据，如果有没发送的就发出去
    for data in self.sendWindow:
      if data.state == 0:
        print(f'客户端发送数据：{data.seq}')
        self.socket.sendto(str(data).encode(),self.serverAddr)
        data.state = 1

    #窗内的数据已经发完，而且不再有新数据，退出
    if len(self.sendWindow) == 0 :
      if pkgTimer > self.maxDelayTime and msg_timer > self.maxWaitTime:
        with open('gbnreceive.txt', 'w',encoding='utf8') as f:
          f.write(self.rev_data)
        print('Client: 发送/接收完毕, 退出')

    #如果确认序号返回超时，把发送窗里的数据状态改成未发送
    if pkgTimer > self.maxDelayTime:
      resend = []
      for data in self.sendWindow:
        data.state = 0
        resend.append(data.seq)
      if len(resend) > 0:
        print('Client: 发生超时，重传',resend)

    readable,writeable,errors = select.select([self.socket, ], [], [], 1) #四个参数监听可读，可写，错误，以及每隔一秒监听一次

    #当服务端发来数据
    if len(readable) > 0:
      message,address = self.socket.recvfrom(1024)
      msg = message.decode()
      if msg[1] == '1': #收到ACK，重新计时
        pkgTimer = 0
        print('Client: 收到ACK ', msg[0])
        ack_num = msg[0]
        for i in range(len(self.sendWindow)):
          if ack_num == self.sendWindow[i].seq:
            self.sendWindow = self.sendWindow[i + 1:] #收到第i个ack，前i个都已经发送成功。
            break
      else: #收到的是数据(全双工通道，两边都在互传message)
        pkgTimer += 1
        print('Client: 收到MSG = ', msg[0])
        ackNum = int(msg[0])
        msg_timer = 0

        if last_ack == ackNum - 1:
          # 丢包率为0.2
          if random() < 0.1:
            print('Client: 模拟发生丢包, 丢失的包的seq为', str(ackNum))
          else:
            if random() < 0.1:
              print('Client: 模拟ACK丢失, 丢失ACK为 ', str(ackNum))
              self.rev_data += msg[2:]
              last_ack = ackNum
          data = Data('', 1, seq=ackNum)
          self.socket.sendto(str(data).encode(),address)
          print('Client: 发送ACK ', str(ackNum))
          last_ack = ackNum
          self.rev_data += msg[2:]

        else:
            print('Client: 收到的MSG不是需要的，发送当前收到的最大的ACK ', last_ack)
            data = Data('', 1, seq=last_ack)
            self.socket.sendto(str(data).encode(),address)
    else:
      pkgTimer += 1
      msg_timer += 1

  def start(self):
    buffer = []
    f = open('client_send.txt', 'r',encoding='utf8')
    seq = f.read(500)
    for i in range(len(seq)):
      buffer.append(seq[i])
    self.socket.sendto('-testgbn'.encode(),self.serverAddr)
    self.send(buffer)


c = Client()
c.start()






