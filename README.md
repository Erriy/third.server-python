# third.server-python


## 部署

### 环境要求

- docker
- docker-compose

### 部署命令

``` shell
docker-compose up -d --build
```

## todo


### web接口服务

- [ ] 全文检索（使用neo4j内置lucene引擎）

  > 目前使用正则查询，速度效率很低，仅供测试使用

- [ ] 服务器管理员接口

  - [ ] 服务器配置
  - [ ] 访问权限管理

### worker

- [ ] 周期性同步数据
  - [ ] 去其他服务器拉取公开数据
  - [ ] 根据用户配置自动推送至用户自定义的
- [ ] 数据变化的消息提醒机制


## 想法

1. 时间分为以下几种：
   1. 创建时间、修改时间、开始时间、结束时间、提醒时间、完成时间