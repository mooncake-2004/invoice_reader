# Invoice Reader

离线 Windows PDF 发票处理工具。

当前版本为阶段 1，只提供：

- 打开单张 PDF；
- 翻页、缩放和滚动；
- 鼠标拖拽框选；
- 实时显示框选区域中的 PDF 文字层文本。

## 运行源码

```powershell
python -m pip install -r requirements.txt
python -m invoice_reader
```

## 阶段 1 EXE 验证

打开 `InvoiceReaderPhase1.exe` 后：

1. 点击“打开 PDF”。
2. 使用“上一页 / 下一页”切换页面。
3. 使用“放大 / 缩小 / 100%”调整预览。
4. 使用鼠标滚轮或滚动条移动页面。
5. 在页面上按住鼠标左键拖拽选择文字区域。
6. 查看右侧“框选文字”区域是否立即显示所选 PDF 文字。

阶段 1 仅支持有文字层的 PDF；OCR、模板、Excel 和归档会在后续阶段加入。
