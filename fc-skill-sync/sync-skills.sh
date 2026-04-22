#!/bin/bash
#
# fc-skill-sync: 同步三个技能目录中的 skills
# 确保每个 skill 只存储一份实体，其他目录通过软链接引用
#

set -euo pipefail

# 定义三个技能目录
DIR_OPENCLAW="${HOME}/.openclaw/skills"
DIR_CLAUDE="${HOME}/.claude/skills"
DIR_AGENTS="${HOME}/.agents/skills"

# 颜色定义
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'

# 统计变量
STAT_CREATED=0
STAT_UPDATED=0
STAT_CONFLICTS=0
STAT_SKIPPED=0
STAT_ERRORS=0

# 日志函数
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[OK]${COLOR_RESET} $1"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

# 确保目录存在
ensure_dir() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    fi
}

# 检查路径是否为软链接
is_symlink() {
    local path="$1"
    [[ -L "$path" ]]
}

# 获取软链接指向的真实路径
get_symlink_target() {
    local path="$1"
    readlink -f "$path" 2>/dev/null || echo "$path"
}

# 获取 skill 的实体目录（返回第一个包含实体文件的目录）
find_source_dir() {
    local skill_name="$1"
    local dirs=("$DIR_OPENCLAW" "$DIR_CLAUDE" "$DIR_AGENTS")

    for dir in "${dirs[@]}"; do
        local skill_path="$dir/$skill_name"
        if [[ -d "$skill_path" ]] && ! is_symlink "$skill_path"; then
            echo "$dir"
            return 0
        fi
    done

    return 1
}

# 同步单个 skill
sync_skill() {
    local skill_name="$1"
    local dirs=("$DIR_OPENCLAW" "$DIR_CLAUDE" "$DIR_AGENTS")

    log_info "处理 skill: $skill_name"

    # 查找实体目录
    local source_dir
    source_dir=$(find_source_dir "$skill_name")

    if [[ -z "$source_dir" ]]; then
        log_error "未找到 $skill_name 的实体目录（全是软链接或不存在）"
        ((STAT_ERRORS++)) || true
        return 1
    fi

    local source_path="$source_dir/$skill_name"
    local source_canonical
    source_canonical=$(get_symlink_target "$source_path")

    log_info "  实体位置: $source_canonical"

    # 在其他目录创建/更新软链接
    for dir in "${dirs[@]}"; do
        local target_path="$dir/$skill_name"

        # 跳过源目录
        if [[ "$dir" == "$source_dir" ]]; then
            continue
        fi

        if [[ -e "$target_path" ]]; then
            if is_symlink "$target_path"; then
                local current_target
                current_target=$(get_symlink_target "$target_path")

                if [[ "$current_target" == "$source_canonical" ]]; then
                    log_info "  已正确链接: $target_path"
                    ((STAT_SKIPPED++)) || true
                else
                    # 更新链接指向
                    rm "$target_path"
                    ln -s "$source_canonical" "$target_path"
                    log_success "  更新链接: $target_path → $source_canonical"
                    ((STAT_UPDATED++)) || true
                fi
            else
                # 存在非链接的文件/目录，需要备份
                local backup_name="${skill_name}.backup.$(date +%Y%m%d_%H%M%S)"
                local backup_path="$dir/$backup_name"
                mv "$target_path" "$backup_path"
                ln -s "$source_canonical" "$target_path"
                log_warn "  备份并链接: $target_path (备份为 $backup_name)"
                ((STAT_CONFLICTS++)) || true
            fi
        else
            # 创建新链接
            ln -s "$source_canonical" "$target_path"
            log_success "  创建链接: $target_path → $source_canonical"
            ((STAT_CREATED++)) || true
        fi
    done
}

# 收集所有 skills
collect_skills() {
    local all_skills=()
    local dirs=("$DIR_OPENCLAW" "$DIR_CLAUDE" "$DIR_AGENTS")

    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            while IFS= read -r -d '' skill_path; do
                local skill_name
                skill_name=$(basename "$skill_path")
                # 跳过以 . 开头的隐藏目录
                if [[ ! "$skill_name" =~ ^\. ]]; then
                    all_skills+=("$skill_name")
                fi
            done < <(find "$dir" -maxdepth 1 -mindepth 1 -type d -print0 2>/dev/null)
        fi
    done

    # 去重并排序
    printf '%s\n' "${all_skills[@]}" | sort -u
}

# 打印报告
print_report() {
    echo ""
    echo "========================================"
    echo "        同步完成报告"
    echo "========================================"
    echo "  新创建链接: $STAT_CREATED"
    echo "  更新链接:   $STAT_UPDATED"
    echo "  跳过(正确): $STAT_SKIPPED"
    echo "  冲突备份:   $STAT_CONFLICTS"
    echo "  错误:       $STAT_ERRORS"
    echo "========================================"
}

# 主函数
main() {
    echo "========================================"
    echo "     fc-skill-sync 技能同步工具"
    echo "========================================"
    echo ""

    # 确保目录存在
    ensure_dir "$DIR_OPENCLAW"
    ensure_dir "$DIR_CLAUDE"
    ensure_dir "$DIR_AGENTS"

    log_info "扫描目录:"
    log_info "  - $DIR_OPENCLAW"
    log_info "  - $DIR_CLAUDE"
    log_info "  - $DIR_AGENTS"
    echo ""

    # 收集所有 skills
    local skills
    skills=$(collect_skills)

    if [[ -z "$skills" ]]; then
        log_warn "未找到任何 skills"
        exit 0
    fi

    local skill_count
    skill_count=$(echo "$skills" | wc -l | tr -d ' ')
    log_info "发现 $skill_count 个 skills，开始同步..."
    echo ""

    # 同步每个 skill
    while IFS= read -r skill_name; do
        sync_skill "$skill_name"
    done <<< "$skills"

    # 打印报告
    print_report

    # 返回状态
    if [[ $STAT_ERRORS -gt 0 ]]; then
        exit 1
    fi

    exit 0
}

# 执行主函数
main "$@"
