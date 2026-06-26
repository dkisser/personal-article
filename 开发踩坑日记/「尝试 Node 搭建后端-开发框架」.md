---
title: "「尝试 Node 搭建后端-开发框架」"
source: "https://note.mowen.cn/detail/w9xqKJNB128ShmPXsDpMz"
author:
published: 2026-06-26
created: 2026-06-26
description: "这篇笔记介绍了使用 Node.js (Fastify + @fastify/awilix) 实现后端开发框架，通过依赖注入容器管理服务，利用 Fastify Hooks 实现面向切面编程（鉴权、错误处理等），并讨论了编程模式演进（从配置驱动到注解驱动）的历史背景。 "
tags:
  - "Node.js"
  - "Fastify"
  - "DI/IOC"
status: "published"
category: "开发踩坑日记"
---
## 「尝试 Node 搭建后端-开发框架」 · 墨问

**「尝试 Node 搭建后端-开发框架」**

昨天搭建的后端只是一个简单的架子，解决的只是最简单的问题-如何启动一个Web服务以及这个服务怎么开发、测试、构建。

而在真实的（或者说Production Ready的）开发场景中，我们常常需要一些开发框架，帮我们解决代码管理上的问题。比如：代码如何保持代码结构的稳定（多实现、减小变更的影响范围等），如何请求层进行拦截（AOP）等等。

说白了，就是后端开发固有的思维模式 IOC、AOP 这些东西在 Node 里面咋做~

这里我使用的是 @fastify/awilix，这并不是注解编程的风格的框架，需要你自己主动感知（或者说是主动选择）使用IOC、DI。

**IOC、DI 的使用**

```
// app.js
const fastify = require('fastify')
const { fastifyAwilixPlugin } = require('@fastify/awilix')

const app = fastify({ logger: true })

app.register(fastifyAwilixPlugin, {
  disposeOnClose: true,
  disposeOnResponse: true,
})

// 后续的注册和路由代码都写在这里

app.listen({ port: 3000 })
```

```
// ---------- 1. 定义服务类 ----------
// services/UserRepository.js
class UserRepository {
  constructor({ dbClient }) {
    this.dbClient = dbClient
  }

  async findUser(id) {
    // 模拟数据库查询
    return { id, name: 'Alice', email: 'alice@example.com' }
  }
}

// services/UserService.js
class UserService {
  constructor({ userRepository, logger }) {
    this.userRepository = userRepository
    this.logger = logger
  }

  async getUser(id) {
    this.logger.info(\`Fetching user: ${id}\`)
    return this.userRepository.findUser(id)
  }
}

// services/Logger.js
class Logger {
  info(msg) { console.log(\`[INFO] ${msg}\`) }
  error(msg) { console.error(\`[ERROR] ${msg}\`) }
}
```

```
// ---------- 2. 注册到 IoC 容器 ----------
const { diContainer } = require('@fastify/awilix')
const { asClass, Lifetime } = require('awilix')

// 注册所有服务（app 级别的单例）
diContainer.register({
  logger: asClass(Logger, { lifetime: Lifetime.SINGLETON }),
  dbClient: asClass(require('./services/DbClient'), { lifetime: Lifetime.SINGLETON }),
  userRepository: asClass(require('./services/UserRepository'), { lifetime: Lifetime.SINGLETON }),
  userService: asClass(require('./services/UserService'), { lifetime: Lifetime.SINGLETON }),
})
```

```
// ---------- 3. 在路由中使用 DI ----------
app.get('/users/:id', async (request, reply) => {
  // 从容器中解析 userService（所有依赖自动注入）
  const userService = app.diContainer.resolve('userService')
  // 或简写：const { userService } = app.diContainer.cradle

  const user = await userService.getUser(request.params.id)
  return { success: true, data: user }
})
```

**AOP的使用**

Fastify 本身支持 Hooks来实现，我这里目前想到的是鉴权、日志、全局异常处理等等

```
export function buildApp(opts?: { logger?: boolean }): FastifyInstance {
  const app = Fastify({
    logger: opts?.logger ?? true,
  });

  app.register(jwt, {
    secret: config.jwtSecret,
    sign: { expiresIn: config.jwtExpiresIn },
  });

  setupAuth(app);

  app.register(authRoutes);
  app.register(healthRoutes);
  app.register(supportRoutes);

  app.setErrorHandler((error, request, reply) => {
    if (error instanceof ApiError) {
      return reply.status(error.statusCode).send({
        status: 'error',
        errorCode: error.errorCode,
        errorMsg: error.message,
      });
    }

    if (error instanceof Error && 'validation' in error) {
      return reply.status(400).send({
        status: 'error',
        errorCode: 'VALIDATION_ERROR',
        errorMsg: error.message,
      });
    }

    request.log.error(error);
    return reply.status(500).send({
      status: 'error',
      errorCode: 'INTERNAL_ERROR',
      errorMsg: 'Internal server error',
    });
  });

  app.setNotFoundHandler((request, reply) => {
    return reply.status(404).send({
      status: 'error',
      errorCode: 'NOT_FOUND',
      errorMsg: \`Route ${request.method} ${request.url} not found\`,
    });
  });

  return app;
}
```

这里我最开始有个疑问，为什么没有使用注解驱动的编程规范？

后来我想了想，发现这里其实隐含了大量历史信息~

在 Java 里 Spring 最开始提倡的是配置驱动，大量的xml配置文件来定义bean的生命周期、依赖关系。直到后来 Spring Boot 流行起来才开始有了现在的注解驱动。

**我感觉这里编程模式其实是随着框架的副产品。** 如果一个框架能流行起来不会是因为他的编程风格特别优雅，而是框架能解决特定的问题，编程风格算是作者的偏好。
