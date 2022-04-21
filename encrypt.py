#encoding=utf-8
from Crypto.Cipher import AES
import base64

def __PKCS5_7Padding(data):
    needSize = 16 - len(data) % 16
    if needSize == 0:
        needSize = 16
    return data + needSize.to_bytes(1, 'little') * needSize

def encodePassword(mpassword,password):
    mpassword=mpassword.encode('utf-8')
    password = password.encode('utf-8')
    #秘钥，b就是表示为bytes类型
    iv = b'btMhfbpCcdxab7ZQ' # iv偏移量，bytes类型
    text = b'JzrhbEw65AdyfGpiYZ6JhsWkyrXp3xZ5A5b2YetknhxkZtR5HAerpdTBZ3ZZNhzi'+mpassword #需要加密的内容，bytes类型
    aes = AES.new(password,AES.MODE_CBC,iv) #创建一个aes对象
    # AES.MODE_CBC 表示模式是CBC模式
    en_text = aes.encrypt(__PKCS5_7Padding(text))
    mpassword=base64.standard_b64encode(en_text).decode('utf-8')
    return mpassword