# SJTU Noticer
SJTU Noticer是一个定期爬去校园咨询并向订阅者发送邮件通知的小工具。

## 准备工作
### 数据库
安装MySQL数据库。
创建Noticer数据库，使用utf8mb4编码。
`CREATE DATABASE Noticer DEFAULT CHARACTER SET utf8mb4`
创建对Noticer拥有ALL Privilege的用户noticer。
`GRANT ALL ON Noticer.* TO 'noticer'@'localhost';`
在src/config里修改相应参数。
