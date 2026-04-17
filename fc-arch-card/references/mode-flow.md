# 流程图/时序图执行步骤

## 1. 判断子类型

根据用户描述判断使用哪种语法：

| 特征 | 推荐类型 | Mermaid 语法 |
|------|----------|--------------|
| 多参与者交互 | 时序图 | `sequenceDiagram` |
| 单线流程、判断分支 | 流程图 | `flowchart TD` |

## 2. 流程图 (flowchart TD)

### 结构模板

```mermaid
flowchart TD
    Start([开始]) --> Step1[步骤1]
    Step1 --> Decision{判断?}
    Decision -->|是| Step2[步骤2]
    Decision -->|否| Step3[步骤3]
    Step2 --> End([结束])
    Step3 --> End
```

### 节点形状

- `[文本]` - 矩形（处理步骤）
- `{文本}` - 菱形（判断）
- `([文本])` - 圆角矩形（开始/结束）
- `[(文本)]` - 圆柱形（数据库）

## 3. 时序图 (sequenceDiagram)

### 结构模板

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Gateway
    participant S as Service
    participant D as Database

    C->>A: HTTP Request
    A->>S: Route Request
    S->>D: Query Data
    D-->>S: Return Data
    S-->>A: JSON Response
    A-->>C: HTTP Response
```

### 消息类型

- `->>` - 实线箭头（同步消息）
- `-->>` - 虚线箭头（返回消息）
- `-x>` - 实线叉（消息丢失）
- `->>+` - 激活 lifeline（开始处理）
- `-->>-` -  deactivate lifeline（结束处理）

## 4. DSL 自检

生成后检查：

- [ ] 流程图：步骤数 ≤ 15
- [ ] 时序图：参与者数 ≤ 6
- [ ] 流程图：有明确开始和结束节点
- [ ] 判断分支：标注条件（是/否 或 success/fail）
- [ ] 时序图：消息有明确方向

## 5. 风格适配

与 mode-arch.md 相同，从 themes.md 读取配置注入 Mermaid init。

## 6. 输出示例

**输入**: "画用户登录流程，包括输入密码、验证、成功或失败跳转"

**输出 DSL (流程图)**:

```mermaid
flowchart TD
    Start([开始]) --> Input[输入用户名密码]
    Input --> Validate{验证}
    Validate -->|成功| Success[跳转首页]
    Validate -->|失败| Error[显示错误]
    Error --> Input
    Success --> End([结束])
```

**输出 DSL (时序图)**:

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant A as Auth Service
    participant DB as Database

    U->>C: 输入用户名密码
    C->>A: POST /login
    A->>DB: 查询用户
    DB-->>A: 返回用户信息
    A->>A: 验证密码
    alt 验证成功
        A-->>C: 返回 Token
        C-->>U: 跳转首页
    else 验证失败
        A-->>C: 401 Unauthorized
        C-->>U: 显示错误
    end
```

## 7. 命名生成

- 用户登录流程图 → `user-login-flow`
- 支付流程时序图 → `payment-process-sequence`
