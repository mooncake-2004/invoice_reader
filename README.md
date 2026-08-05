# Invoice Reader

离线 Windows PDF 发票处理工具。

当前版本为阶段 1，只提供：

- 打开单张 PDF；
- 鼠标滚轮翻页、缩放和滚动条移动；
- 鼠标拖拽多个框选并显示序号；
- 右侧按序号实时显示每个框选区域中的 PDF 文字层文本；
- 点击框选后按 Delete 删除。

## 运行源码

```powershell
python -m pip install -r requirements.txt
python -m invoice_reader
```

## 阶段 1 EXE 验证

打开 `InvoiceReaderPhase1.exe` 后：

1. 点击“打开 PDF”。
2. 向下滚动鼠标滚轮查看下一页，向上滚动查看上一页。
3. 使用“放大 / 缩小 / 100%”调整预览；需要时使用滚动条移动页面。
4. 在页面上按住鼠标左键拖拽多个文字区域，确认每个框显示序号。
5. 查看右侧“框选文字”区域是否按序号显示每个框的文字。
6. 点击一个框后按 Delete，确认该框和对应右侧文字都被删除并重新编号。

阶段 1 仅支持有文字层的 PDF；OCR、模板、Excel 和归档会在后续阶段加入。
