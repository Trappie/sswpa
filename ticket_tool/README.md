# Ticket Information Formatter Tool

一个本地Python工具，用于从JSON文件生成格式化的markdown文件，用于更新票务信息中的演奏会曲目。

## 功能

- 从 `program.json` 读取曲目信息
- 支持曲目（piece）和中场休息（intermission）两种类型
- 生成格式化的 `program.md` 文件

## 使用方法

### 1. 准备program.json文件

在 `ticket_tool` 目录下创建 `program.json` 文件，格式如下：

```json
{
  "items": [
    {
      "type": "piece",
      "title": "作品标题",
      "composer": "作曲家姓名",
      "years": "1882-1971",
      "movements": ["第一乐章", "第二乐章"]
    },
    {
      "type": "intermission"
    },
    {
      "type": "piece",
      "title": "另一首作品",
      "composer": "另一位作曲家",
      "years": "1756-1791"
    }
  ]
}
```

**字段说明：**

- `items`: 数组，按演出顺序排列
- 曲目（`type: "piece"`）必须包含：
  - `title`: 作品标题（字符串）
  - `composer`: 作曲家姓名（字符串）
  - `years`: 作曲家生卒年（字符串，格式如"1882-1971"）
  - `movements`: 可选，乐章列表（字符串数组）
- 中场休息（`type: "intermission"`）只需类型字段

### 2. 运行脚本

```bash
# 使用当前目录下的program.json（默认）
python ticket_tool/format_ticket.py

# 或指定JSON文件路径
python ticket_tool/format_ticket.py /path/to/program.json
```

### 3. 查看输出

脚本会在 `ticket_tool` 目录下生成 `program.md` 文件。

## 示例

参考 `example_program.json` 查看完整的示例格式。

运行示例：

```bash
# 复制示例文件
cp ticket_tool/example_program.json ticket_tool/program.json

# 运行脚本
python ticket_tool/format_ticket.py
```

生成的 `program.md` 示例：

```markdown
**Wolfgang Amadeus Mozart** (1756-1791)
Sonata in C Major, K. 330
- Allegro moderato
- Andante cantabile
- Allegretto

**Frédéric Chopin** (1810-1849)
Ballade No. 1 in G minor, Op. 23

---

**中场休息**

---

**Ludwig van Beethoven** (1770-1827)
Piano Sonata No. 14 in C-sharp minor, Op. 27, No. 2
- Adagio sostenuto
- Allegretto
- Presto agitato

**Maurice Ravel** (1875-1937)
La Valse
```

## 错误处理

脚本会验证JSON格式和必需字段，如果发现问题会显示清晰的错误信息：

- 文件不存在
- JSON格式错误
- 缺少必需字段
- 字段类型错误
- 空值检查

## 注意事项

- 确保使用UTF-8编码保存JSON文件
- 乐章（movements）是可选的，如果曲目没有乐章可以省略
- 曲目按 `items` 数组的顺序生成
- 每个曲目之间会自动添加空行分隔
