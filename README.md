# 采购三方勾稽报告

面向真实数据复核的中型数据工程工具，包含七个可独立调用的业务模块。规则、失败原因与证据字段见 docs/DATA-DICTIONARY.md，陷阱和测试映射见 docs/DEPTH.md。

## 启动

docker compose up --build

浏览器访问 http://localhost:18218。测试：docker compose exec -T app pytest -q

## 模块

- M1 单据采信：页面 /documents，接口 /api/documents/import
- M2 主数据映射：页面 /master，接口 /api/master/resolve
- M3 数量勾稽：页面 /quantity，接口 /api/quantity/match
- M4 税额核验：页面 /tax，接口 /api/tax/check
- M5 多对多匹配：页面 /matching，接口 /api/matches/solve
- M6 差异批次：页面 /batches，接口 /api/reconcile
- M7 退货红票：页面 /returns，接口 /api/returns/register（批号补齐 /api/returns/supplement，台账 /api/returns）

## M7 退货红票规则

仓库退货只登记货号与箱数、未登记原收货批号，而货号存在多版装箱规格（如老包装 12 件/箱、新包装 10 件/箱）时：

1. 主数据全部有效装箱规格参与勾稽，给出退货件数区间（10～12 件）。
2. 批号缺失当天按**最小装箱规格**保守折算红票件数（1 箱按 10 件），只冲可证明部分的税（130.00 元），差额（2 件 / 26.00 元）挂账，避免多冲税款。
3. 晚到的收货批号补齐后，按批号对应的实际包装追加冲税；追加额只对“实际件数−已覆盖件数”的差额计税。
4. 退货单号与运行标识双重幂等：重跑同一笔退货或同一批补齐请求复用既有台账，绝不重复冲税。

## 运行规则

同一输入内容生成相同运行标识，重复执行复用已有批次。隔离记录包含原因码、原始行号与原值；业务导出只保留一份证据清单。

