#!/usr/bin/env python3
"""
Doc Converter - 批量文档转 Markdown 工具

使用 markitdown 将办公文档（PDF、PPT、Word、Excel 等）批量转换为 Markdown，
生成 CSV 索引供 Claude 后续分析、摘要和思维导图分类。
"""

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# 支持的文件格式
SUPPORTED_EXTENSIONS = {
    ".pdf", ".pptx", ".docx", ".xlsx", ".xls",
    ".csv", ".html", ".htm", ".epub",
    ".json", ".xml",
}

# 扫描时排除的目录
EXCLUDED_DIRS = {
    ".git", ".svn", ".hg",
    ".cache", ".npm", ".yarn", ".pnpm",
    ".venv", "venv", "env", ".env",
    "__pycache__", ".pytest_cache",
    "node_modules", "vendor", "packages",
    "Library", ".Trash",
    ".idea", ".vscode", ".vs",
    "build", "dist", "target", "out",
    ".summaries",
}


@dataclass
class DocInfo:
    """文档信息"""
    original_path: str
    file_type: str
    file_size: int
    file_size_human: str = ""
    markdown_path: str = ""
    conversion_status: str = "pending"
    error_message: str = ""
    converted_at: str = ""


@dataclass
class ConvertReport:
    """转换报告"""
    scan_time: str
    source_paths: list = field(default_factory=list)
    documents: list = field(default_factory=list)
    total_files: int = 0
    total_size_bytes: int = 0
    total_size_human: str = ""
    converted_count: int = 0
    failed_count: int = 0
    summaries_dir: str = ""


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def check_markitdown() -> bool:
    """检查 markitdown 是否已安装"""
    try:
        import markitdown  # noqa: F401
        return True
    except ImportError:
        return False


class DocConverter:
    """文档批量转换器"""

    def __init__(self, paths: list[str]):
        self.paths = [os.path.expanduser(p) for p in paths]
        self.documents: list[DocInfo] = []

    def _should_exclude(self, path: Path) -> bool:
        """检查是否应该排除该路径"""
        for part in path.parts:
            if part in EXCLUDED_DIRS:
                return True
        return False

    def _get_summaries_dir(self) -> str:
        """获取 .summaries 输出目录（基于第一个路径）"""
        first = Path(self.paths[0])
        if first.is_file():
            base = first.parent
        else:
            base = first
        return str(base / ".summaries")

    def scan(self) -> list[DocInfo]:
        """扫描所有路径，收集支持的文档"""
        self.documents = []

        for path_str in self.paths:
            path = Path(path_str)

            if not path.exists():
                print(f"  ⚠️  路径不存在: {path_str}")
                continue

            if path.is_file():
                self._add_file(path)
            elif path.is_dir():
                self._scan_dir(path)

        # 按文件大小降序排序
        self.documents.sort(key=lambda d: d.file_size, reverse=True)
        return self.documents

    def _scan_dir(self, directory: Path):
        """递归扫描目录"""
        try:
            for item in sorted(directory.iterdir()):
                if item.is_dir():
                    if item.name.startswith(".") or item.name in EXCLUDED_DIRS:
                        continue
                    self._scan_dir(item)
                elif item.is_file():
                    self._add_file(item)
        except PermissionError:
            print(f"  ⚠️  无权限访问: {directory}")

    def _add_file(self, path: Path):
        """添加单个文件"""
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return

        try:
            size = path.stat().st_size
        except OSError:
            return

        doc = DocInfo(
            original_path=str(path),
            file_type=ext,
            file_size=size,
            file_size_human=format_size(size),
        )
        self.documents.append(doc)

    def preview(self, use_json: bool = False) -> ConvertReport:
        """预览模式：列出将要转换的文档"""
        if not self.documents:
            self.scan()

        report = ConvertReport(
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source_paths=self.paths,
            documents=self.documents,
            total_files=len(self.documents),
            total_size_bytes=sum(d.file_size for d in self.documents),
            summaries_dir=self._get_summaries_dir(),
        )
        report.total_size_human = format_size(report.total_size_bytes)

        if use_json:
            print(json.dumps({
                "scan_time": report.scan_time,
                "source_paths": report.source_paths,
                "total_files": report.total_files,
                "total_size": report.total_size_human,
                "summaries_dir": report.summaries_dir,
                "documents": [
                    {
                        "path": d.original_path,
                        "type": d.file_type,
                        "size": d.file_size_human,
                        "size_bytes": d.file_size,
                    }
                    for d in self.documents
                ],
            }, indent=2, ensure_ascii=False))
        else:
            print(f"📂 扫描路径: {', '.join(self.paths)}")
            print(f"📊 找到 {report.total_files} 个文档, 共 {report.total_size_human}")
            print(f"📁 输出目录: {report.summaries_dir}")
            print("")

            # 按文件类型分组统计
            by_type: dict[str, list[DocInfo]] = {}
            for doc in self.documents:
                by_type.setdefault(doc.file_type, []).append(doc)

            type_icons = {
                ".pdf": "📄", ".pptx": "📊", ".docx": "📝",
                ".xlsx": "📈", ".xls": "📈", ".csv": "📈",
                ".html": "🌐", ".htm": "🌐", ".epub": "📚",
                ".json": "📋", ".xml": "📋",
            }

            for ext, docs in sorted(by_type.items(), key=lambda x: -len(x[1])):
                icon = type_icons.get(ext, "📄")
                total_size = sum(d.file_size for d in docs)
                print(f"  {icon} {ext}: {len(docs)} 个, {format_size(total_size)}")

            if self.documents:
                print("")
                print("📋 文件列表:")
                for i, doc in enumerate(self.documents, 1):
                    icon = type_icons.get(doc.file_type, "📄")
                    name = Path(doc.original_path).name
                    print(f"  {i:3d}. {icon} {name} ({doc.file_size_human})")

        return report

    def convert(self, use_json: bool = False) -> ConvertReport:
        """执行转换"""
        if not self.documents:
            self.scan()

        if not self.documents:
            print("ℹ️  没有可转换的文档")
            return ConvertReport(
                scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source_paths=self.paths,
            )

        # 检查 markitdown
        if not check_markitdown():
            print("❌ markitdown 未安装")
            print("   请运行: pip install 'markitdown[all]'")
            sys.exit(1)

        from markitdown import MarkItDown

        md_converter = MarkItDown()

        # 创建输出目录
        summaries_dir = self._get_summaries_dir()
        converted_dir = os.path.join(summaries_dir, "converted")
        briefs_dir = os.path.join(summaries_dir, "briefs")
        os.makedirs(converted_dir, exist_ok=True)
        os.makedirs(briefs_dir, exist_ok=True)

        report = ConvertReport(
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source_paths=self.paths,
            documents=self.documents,
            total_files=len(self.documents),
            total_size_bytes=sum(d.file_size for d in self.documents),
            summaries_dir=summaries_dir,
        )
        report.total_size_human = format_size(report.total_size_bytes)

        if not use_json:
            print(f"🔄 开始转换 {report.total_files} 个文档...")
            print(f"📁 输出目录: {summaries_dir}")
            print("")

        for i, doc in enumerate(self.documents, 1):
            name = Path(doc.original_path).stem
            ext = doc.file_type
            md_filename = f"{name}{ext}.md"
            md_path = os.path.join(converted_dir, md_filename)

            if not use_json:
                print(f"  [{i}/{report.total_files}] 转换: {Path(doc.original_path).name}...", end=" ")

            try:
                result = md_converter.convert(doc.original_path)
                content = result.text_content if result.text_content else ""

                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(f"# {name}\n\n")
                    f.write(f"> 原始文件: {doc.original_path}\n")
                    f.write(f"> 文件类型: {ext} | 大小: {doc.file_size_human}\n")
                    f.write(f"> 转换时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(content)

                doc.markdown_path = md_path
                doc.conversion_status = "success"
                doc.converted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                report.converted_count += 1

                if not use_json:
                    print("✅")

            except Exception as e:
                doc.conversion_status = "failed"
                doc.error_message = str(e)
                report.failed_count += 1

                if not use_json:
                    print(f"❌ {e}")

        # 生成 CSV 索引
        csv_path = os.path.join(summaries_dir, "index.csv")
        self._write_csv(csv_path)

        if use_json:
            print(json.dumps({
                "scan_time": report.scan_time,
                "source_paths": report.source_paths,
                "total_files": report.total_files,
                "total_size": report.total_size_human,
                "converted": report.converted_count,
                "failed": report.failed_count,
                "summaries_dir": summaries_dir,
                "index_csv": csv_path,
                "documents": [
                    {
                        "original_path": d.original_path,
                        "markdown_path": d.markdown_path,
                        "file_type": d.file_type,
                        "size": d.file_size_human,
                        "status": d.conversion_status,
                        "error": d.error_message,
                    }
                    for d in self.documents
                ],
            }, indent=2, ensure_ascii=False))
        else:
            print("")
            print(f"✅ 转换完成: {report.converted_count} 成功, {report.failed_count} 失败")
            print(f"📄 CSV 索引: {csv_path}")
            print(f"📁 Markdown 文件: {converted_dir}")
            print(f"📁 摘要目录（待 Claude 生成）: {briefs_dir}")

        return report

    def _write_csv(self, csv_path: str):
        """写入 CSV 索引"""
        fieldnames = [
            "original_path", "markdown_path", "file_type",
            "file_size", "conversion_status", "error_message", "converted_at",
        ]

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for doc in self.documents:
                writer.writerow({
                    "original_path": doc.original_path,
                    "markdown_path": doc.markdown_path,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "conversion_status": doc.conversion_status,
                    "error_message": doc.error_message,
                    "converted_at": doc.converted_at,
                })


def main():
    parser = argparse.ArgumentParser(
        description="Doc Converter - 批量文档转 Markdown 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ~/Documents/reports --preview          # 预览文档列表
  %(prog)s ~/Documents/reports --convert --confirm # 执行转换
  %(prog)s file1.pdf file2.pptx --convert --confirm # 转换指定文件
  %(prog)s ~/Documents --preview --json            # JSON 格式预览

支持格式: .pdf, .pptx, .docx, .xlsx, .xls, .csv, .html, .epub, .json, .xml
        """
    )

    parser.add_argument("paths", nargs="+", help="文件或目录路径")
    parser.add_argument("--preview", action="store_true", help="预览模式，列出文档")
    parser.add_argument("--convert", action="store_true", help="执行转换")
    parser.add_argument("--confirm", action="store_true", help="确认执行（安全机制）")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    if not args.preview and not args.convert:
        parser.print_help()
        return

    converter = DocConverter(args.paths)

    if args.preview:
        converter.preview(use_json=args.json)
        return

    if args.convert:
        if not args.confirm:
            print("❌ 转换需要 --confirm 参数确认")
            print("   请先使用 --preview 预览，确认后添加 --confirm 执行转换")
            return

        # 先检查 markitdown
        if not check_markitdown():
            print("❌ markitdown 未安装")
            print("   请运行: pip install 'markitdown[all]'")
            sys.exit(1)

        converter.convert(use_json=args.json)


if __name__ == "__main__":
    main()
