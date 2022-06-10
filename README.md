# VeighNa框架的TimescaleDB数据库接口

<p align="center">
  <img src ="https://vnpy.oss-cn-shanghai.aliyuncs.com/vnpy-logo.png"/>
</p>

<p align="center">
    <img src ="https://img.shields.io/badge/version-1.0.0-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux-yellow.svg"/>
    <img src ="https://img.shields.io/badge/python-3.7｜3.9｜3.9｜3.10-blue.svg" />
</p>

## 说明

基于timescaledb2.7.0开发的TimescaleDB时序数据库接口，使用前需要在postgres添加timescaledb扩展。

## 使用

在veighna中使用TimescaleDB时，需要在全局配置中填写以下字段信息：

|名称|含义|必填|举例|
|---------|----|---|---|
|database.name|名称|是|timescaledb|
|database.host|地址|是|localhost|
|database.port|端口|是|5432|
|database.database|实例|是|vnpy|
|database.user|用户名|是|postgres|
|database.password|密码|是|    |
