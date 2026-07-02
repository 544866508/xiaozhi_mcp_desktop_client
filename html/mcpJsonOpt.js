/**
 * 独立工具：优化单行MCP输入JSON
 * @param {string} jsonString 用户输入原始JSON字符串
 * @returns {object} 清洗后的单层MCP对象 {名称:{配置}}
 */
function optimizeSingleMcpJson(jsonString) {
    let obj = JSON.parse(jsonString);

    // 规则1：外层如果包含 mcpServers，剥离一层只保留内部对象
    if (obj.mcpServers && typeof obj.mcpServers === 'object' && !Array.isArray(obj.mcpServers)) {
        obj = obj.mcpServers;
    }

    // 规则2：遍历第二层配置，替换字段映射
    const fieldMap = {
        baseUrl: 'url',
        httpUrl: 'url',
        desc: 'description'
    };
    for (const serverName of Object.keys(obj)) {
        const serverCfg = obj[serverName];
        if (typeof serverCfg !== 'object' || serverCfg === null) continue;

        // 遍历映射表替换字段
        for (const oldKey in fieldMap) {
            const newKey = fieldMap[oldKey];
            if (serverCfg.hasOwnProperty(oldKey)) {
                serverCfg[newKey] = serverCfg[oldKey];
                delete serverCfg[oldKey];
            }
        }
    }

    return obj;
}

/**
 * 传入已有key数组 + 原始名称，直接返回永不重复的最终名称
 * 自动识别后缀(2)/(3)并递进
 * @param {string[]} existKeys 已存在全部MCP名称数组
 * @param {string} targetKey 用户原始名称
 * @returns {string} 无冲突可用名称
 */
function getSafeNewMcpKey(existKeys, targetKey) {
    // 完全匹配不存在直接返回原名称
    if (!existKeys.includes(targetKey)) {
        return targetKey;
    }

    // 拆分基础名与当前数字，支持 xxx、xxx(2)、xxx(10) 格式
    let baseName = targetKey;
    let startNum = 2;
    const reg = /^(.+)\((\d+)\)$/;
    const match = targetKey.match(reg);
    if (match) {
        baseName = match[1];
        startNum = parseInt(match[2], 10) + 1;
    }

    // 循环找第一个不冲突后缀
    let finalName;
    for (let n = startNum; ; n++) {
        finalName = `${baseName}(${n})`;
        if (!existKeys.includes(finalName)) {
            break;
        }
    }
    return finalName;
}