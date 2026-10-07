#!/usr/bin/env python3
"""Validate anonymous research artifacts and generate an offline HTML report."""
import argparse
import csv
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

SKILL = Path(__file__).resolve().parents[1]
REQUIRED = {'sample_id', 'platform', 'quote', 'source_url', 'relevance', 'sentiment'}
OPTIONAL = ('brand model published_at software_version identity_status source_title scope batch relevance_reason display_quote additional_quote user_job desired_outcome_inferred primary_theme limitations live_recheck theme usage_scene pain_point task_impact evidence_strength evidence_basis').split()
NEED_FIELDS = {'need_id', 'priority', 'need', 'theme_id', 'evidence_ids', 'reason', 'decision_type', 'insight', 'suggested_action', 'validation', 'confidence'}


def csv_read(path, required):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path.name}: 缺少字段 {sorted(missing)}')
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f'{path.name}: CSV列数错误')
    return rows


def safe_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('来源必须为无凭据的HTTP(S)链接')


def encode(value):
    # Prevent source text from closing script tags or becoming executable HTML.
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def render(project, title, output):
    rows = csv_read(project / 'data/feedback.csv', REQUIRED)
    ids = set()
    related = set()
    for row in rows:
        ident = row['sample_id']
        if not ident or ident in ids:
            raise ValueError('记录ID为空或重复')
        ids.add(ident)
        if not row['quote'].strip() or not row['platform'].strip():
            raise ValueError(f'{ident}: 缺少原声或平台')
        safe_url(row['source_url'])
        if row['sentiment'] not in {'正面', '负面', '混合', '中性', '未标注'}:
            raise ValueError(f'{ident}: 无效情绪')
        if row['relevance'] not in {'相关', '不相关', '待审核'}:
            raise ValueError(f'{ident}: 无效相关性')
        for field in OPTIONAL:
            row.setdefault(field, '')
        if row['published_at']:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', row['published_at']):
                raise ValueError(f'{ident}: 日期需YYYY-MM-DD')
            date.fromisoformat(row['published_at'])
        if row['relevance'] == '相关':
            related.add(ident)
            for field in ('theme', 'usage_scene', 'pain_point', 'task_impact', 'evidence_strength', 'evidence_basis'):
                if not row[field].strip():
                    raise ValueError(f'{ident}: 相关反馈未完成 {field} 标注')
            if row['evidence_strength'] not in {'高', '中', '低'}:
                raise ValueError(f'{ident}: 无效证据强度')
    needs = csv_read(project / 'data/needs.csv', NEED_FIELDS)
    need_ids = set()
    for need in needs:
        if not need['need_id'] or need['need_id'] in need_ids:
            raise ValueError('需求ID为空或重复')
        need_ids.add(need['need_id'])
        if need['priority'] not in {'P0', 'P1', 'P2'}:
            raise ValueError('无效需求优先级')
        evidence = [x.strip() for x in need['evidence_ids'].split(',') if x.strip()]
        if not evidence or set(evidence) - related:
            raise ValueError(f"{need['need_id']}: 需求引用不存在或未纳入主题")
        need['evidence_ids'] = ','.join(evidence)
    audit = csv_read(project / 'data/source_audit.csv', {'source_id', 'url', 'status', 'decision', 'sample_ids'})
    for source in audit:
        if source['url']:
            safe_url(source['url'])
        else:
            source['url'] = '#'  # Failed searches may not have a source URL.
    reports = {key: (project / 'docs' / filename).read_text(encoding='utf-8') for key, filename in [('report', '01-数据分析报告.md'), ('mrd', '02-MRD.md')]}
    summary_text = (project / 'docs/03-洞察总结.md').read_text(encoding='utf-8').strip().splitlines()
    if not summary_text:
        raise ValueError('缺少AI洞察总结')
    summary = {'heading': summary_text[0].lstrip('# ').strip(), 'text': '\n'.join(summary_text[1:]).strip()}
    page = (SKILL / 'assets/template.html').read_text(encoding='utf-8')
    # One substitution pass: user text cannot inject another template token.
    replacements = {'__REVIEW_DATA__': encode(rows), '__NEED_DATA__': encode(needs), '__AUDIT_DATA__': encode(audit), '__REPORT_DATA__': encode(reports), '__SUMMARY_DATA__': encode(summary), '__RESEARCH_TITLE__': html.escape(title)}
    page = re.sub('|'.join(map(re.escape, replacements)), lambda m: replacements[m.group()], page)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    return {'html': str(output), 'collected': len(rows), 'related': len(related), 'needs': len(needs)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    output = args.output.resolve() if args.output else project / 'research.html'
    if output.suffix.lower() != '.html':
        parser.error('输出文件必须是HTML')
    if output.exists():
        parser.error('输出已存在；请选择新文件名，避免覆盖已有页面')
    try:
        print(json.dumps(render(project, args.title, output), ensure_ascii=False))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'生成失败：{exc}\n')


if __name__ == '__main__':
    main()
