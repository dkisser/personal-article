---
title: "「一个简化AI代码的小技巧」"
source: "https://note.mowen.cn/detail/w-54okTBZsF6KiptyflyJ"
author:
published: 2026-06-01
created: 2026-06-01
description: "本文介绍了两条简化AI代码的小技巧：卫句模式（优先处理不符合条件的情况并提前返回）和组合方法（将方法拆分为多个意图清晰的小函数）。通过对比深层嵌套代码和改进后的简洁代码，展示了如何让代码更易读。同时提醒Python高级语法如lambda需谨慎使用。 "
tags:
  - "代码技巧"
  - "编程风格"
  - "AI代码"
status: "published"
category: "经验总结"

---
## 「一个简化AI代码的小技巧」 · 墨问

**「一个简化AI代码的小技巧」**

平时大家用 Coding Agent 的时候有没有发现，代码时不时地就会又臭又长？

今天分享卫句模式和组合方法这两种我常用的编程风格来简化你的AI代码，减轻你在 CR 时的负担。

**卫句模式（Guard Clause）**

核心思想是： **优先处理不符合条件的情况，一旦遇到就提前返回或退出** 。这样可以让主要逻辑保持清晰、平铺，减少“箭头型代码”，避免深层嵌套。

```
def calculate_discount(price, member_level, is_new_user):
    if price > 0:
        if is_new_user:
            discount = 0.8
            final_price = price * discount
            return final_price
        else:
            if member_level == 'normal':
                discount = 0.9
                final_price = price * discount
                return final_price
            elif member_level == 'gold':
                discount = 0.85
                final_price = price * discount
                return final_price
            else:
                return price  # 无折扣
    else:
        return "价格无效"
```

上面就是典型的深层次嵌套代码，逻辑上没问题，就是在理解的时候，眼花缭乱。

```
def calculate_discount(price, member_level, is_new_user):
    # 卫句：先处理无效情况
    if price <= 0:
        return "价格无效"

    # 卫句：新用户特殊处理
    if is_new_user:
        return price * 0.8

    # 卫句：会员等级处理
    if member_level == 'normal':
        return price * 0.9
    if member_level == 'gold':
        return price * 0.85

    # 默认情况（非会员也不是新用户）
    return price
```

你会发现，逻辑上是一样的，但是看上去就很简洁。

**组合方法（Composed Method）**

Kent Beck 在《Smalltalk Best Practice Patterns》中提出的模式：一个方法应由一系列意图明确的、粒度很小的子方法调用组成，每个子方法做一件事且命名清晰。这让你读主函数就像读步骤清单一样。

下面是反例

```
def process_order(order):
    # 计算税费（5行）
    tax = order.subtotal * 0.08
    if order.state == 'CA':
        tax += order.subtotal * 0.02
    # 计算运费（4行）
    if order.subtotal < 50:
        shipping = 5.99
    else:
        shipping = 0
    # 格式化输出（3行）
    total = order.subtotal + tax + shipping
    return f"${total:.2f}"
```

改进后

```
# 函数主入口
def process_order(order):
    tax = _calculate_tax(order)
    shipping = _calculate_shipping(order)
    total = order.subtotal + tax + shipping
    return _format_currency(total)

def _calculate_tax(order):
    tax = order.subtotal * 0.08
    if order.state == 'CA':
        tax += order.subtotal * 0.02
    return tax

def _calculate_shipping(order):
    return 5.99 if order.subtotal < 50 else 0

def _format_currency(amount):
    return f"${amount:.2f}"
```

当然，很多高版本的语法也能简化。比如 python 中的 lambda、列表推导式这两个在处理数据的时候也很方便（lambda慎用，有时候写的又臭又长，更难理解）
