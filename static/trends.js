// trends.js - 詐騙趨勢地圖頁面 JavaScript

// ⚠️ 重要：請將此 LIFF ID 替換為你在 LINE Developers Console 建立的 LIFF ID
const LIFF_ID_TRENDS = "2009609029-RlBZuNs2"; // 趨勢地圖頁面 LIFF ID
const API_BASE_URL = window.location.origin;

// ==================== LIFF 初始化 ====================

async function initializeLiff() {
    try {
        console.log("正在初始化 LIFF...");
        await liff.init({ liffId: LIFF_ID_TRENDS });
        
        console.log("LIFF 初始化成功");
        
        // 不需要登入也能查看趨勢地圖
        await loadTrends();
        
    } catch (error) {
        console.error("LIFF 初始化失敗:", error);
        // 即使 LIFF 初始化失敗，仍然載入趨勢地圖
        await loadTrends();
    }
}

// ==================== 載入趨勢資料 ====================

async function loadTrends() {
    try {
        // 呼叫 API 取得趨勢資料
        const response = await fetch(`${API_BASE_URL}/api/trends/domains`);
        
        if (!response.ok) {
            throw new Error("無法取得趨勢資料");
        }
        
        const data = await response.json();
        const domains = data.domains;
        
        console.log(`取得 ${domains.length} 個網域`);
        
        // 隱藏 loading
        document.getElementById('trends-loading').classList.add('hidden');
        
        if (domains.length === 0) {
            // 顯示空狀態
            document.getElementById('empty-state').classList.remove('hidden');
        } else {
            // 計算統計資訊
            const totalDomains = domains.length;
            const totalReports = domains.reduce((sum, d) => sum + d.report_count, 0);
            const avgRisk = (domains.reduce((sum, d) => sum + (d.avg_risk_score * d.report_count), 0) / totalReports).toFixed(1);
            
            // 顯示統計摘要
            document.getElementById('total-domains').textContent = totalDomains;
            document.getElementById('total-reports').textContent = totalReports;
            document.getElementById('avg-risk').textContent = avgRisk;
            document.getElementById('stats-summary').classList.remove('hidden');
            
            // 渲染趨勢列表
            renderTrends(domains);
            document.getElementById('trends-list').classList.remove('hidden');
        }
        
        // 顯示主要內容
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-content').classList.remove('hidden');
        
    } catch (error) {
        console.error("載入趨勢資料失敗:", error);
        document.getElementById('trends-loading').innerHTML = 
            '<p class="text-red-500 text-center">載入失敗: ' + error.message + '</p>';
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-content').classList.remove('hidden');
    }
}

// ==================== 渲染趨勢列表 ====================

function renderTrends(domains) {
    const container = document.getElementById('domains-container');
    container.innerHTML = '';
    
    // 找出最大通報次數（用於計算相對寬度）
    const maxReports = Math.max(...domains.map(d => d.report_count));
    
    domains.forEach((domain, index) => {
        const domainCard = createDomainCard(domain, maxReports);
        container.appendChild(domainCard);
    });
}

function createDomainCard(domain, maxReports) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition';
    
    // 計算通報次數的相對寬度（用於視覺化）
    const widthPercent = (domain.report_count / maxReports) * 100;
    
    // 根據風險評分決定顏色
    let riskColor = 'bg-green-500';
    let riskTextColor = 'text-green-600';
    let riskLabel = '低風險';
    
    if (domain.avg_risk_score >= 7) {
        riskColor = 'bg-red-500';
        riskTextColor = 'text-red-600';
        riskLabel = '高風險';
    } else if (domain.avg_risk_score >= 4) {
        riskColor = 'bg-orange-500';
        riskTextColor = 'text-orange-600';
        riskLabel = '中風險';
    }
    
    // 排名徽章
    let rankBadge = '';
    if (domain.rank === 1) {
        rankBadge = '<span class="text-2xl mr-2">🥇</span>';
    } else if (domain.rank === 2) {
        rankBadge = '<span class="text-2xl mr-2">🥈</span>';
    } else if (domain.rank === 3) {
        rankBadge = '<span class="text-2xl mr-2">🥉</span>';
    } else {
        rankBadge = `<span class="text-gray-500 font-bold mr-2">#${domain.rank}</span>`;
    }
    
    card.innerHTML = `
        <div class="flex items-start justify-between mb-3">
            <div class="flex items-center flex-1 min-w-0">
                ${rankBadge}
                <div class="flex-1 min-w-0">
                    <h3 class="font-bold text-gray-800 truncate" title="${escapeHtml(domain.domain)}">
                        ${escapeHtml(domain.domain)}
                    </h3>
                    <p class="text-xs text-gray-500 mt-1">
                        被通報 ${domain.report_count} 次
                    </p>
                </div>
            </div>
            <div class="text-right ml-4">
                <p class="text-2xl font-black ${riskTextColor}">${domain.avg_risk_score}</p>
                <p class="text-xs text-gray-500">${riskLabel}</p>
            </div>
        </div>
        
        <!-- 通報次數視覺化 -->
        <div class="mb-2">
            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div class="${riskColor} h-full rounded-full transition-all duration-500" style="width: ${widthPercent}%"></div>
            </div>
        </div>
        
        <!-- 風險評分條 -->
        <div class="flex items-center space-x-2 text-xs text-gray-500">
            <span>風險評分:</span>
            <div class="flex-1 bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div class="${riskColor} h-full rounded-full" style="width: ${(domain.avg_risk_score / 10) * 100}%"></div>
            </div>
            <span>${domain.avg_risk_score}/10</span>
        </div>
    `;
    
    return card;
}

// ==================== 輔助函數 ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== 啟動 LIFF ====================

initializeLiff();
