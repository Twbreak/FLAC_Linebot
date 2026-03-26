// team-leaderboard.js - 團隊排行榜頁面 JavaScript

// ⚠️ 重要：請將此 LIFF ID 替換為你在 LINE Developers Console 建立的 LIFF ID
const LIFF_ID_LEADERBOARD = "2009609029-RlBZuNs2"; // 排行榜頁面 LIFF ID
const API_BASE_URL = window.location.origin;

// 全域變數
let currentUser = null;
let expandedTeams = new Set(); // 記錄已展開的團隊

// ==================== LIFF 初始化 ====================

async function initializeLiff() {
    try {
        console.log("正在初始化 LIFF...");
        await liff.init({ liffId: LIFF_ID_LEADERBOARD });
        
        console.log("LIFF 初始化成功");
        
        if (!liff.isLoggedIn()) {
            console.log("使用者未登入，導向登入頁面");
            liff.login();
        } else {
            console.log("使用者已登入，載入排行榜");
            await loadLeaderboard();
        }
    } catch (error) {
        console.error("LIFF 初始化失敗:", error);
        // 即使 LIFF 初始化失敗，仍然載入排行榜（不需要登入也能查看）
        await loadLeaderboard();
    }
}

// ==================== 載入排行榜 ====================

async function loadLeaderboard() {
    try {
        // 取得使用者資料（如果已登入）
        if (liff.isLoggedIn()) {
            try {
                currentUser = await liff.getProfile();
                console.log("使用者資料:", currentUser);
            } catch (error) {
                console.log("無法取得使用者資料，繼續載入排行榜");
            }
        }
        
        // 呼叫 API 取得排行榜
        const response = await fetch(`${API_BASE_URL}/api/leaderboard/teams`);
        
        if (!response.ok) {
            throw new Error("無法取得排行榜資料");
        }
        
        const data = await response.json();
        const teams = data.teams;
        
        console.log(`取得 ${teams.length} 個團隊`);
        
        // 隱藏 loading
        document.getElementById('leaderboard-loading').classList.add('hidden');
        
        if (teams.length === 0) {
            // 顯示空狀態
            document.getElementById('empty-state').classList.remove('hidden');
        } else {
            // 渲染排行榜
            renderLeaderboard(teams);
            document.getElementById('leaderboard-list').classList.remove('hidden');
        }
        
        // 顯示主要內容
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-content').classList.remove('hidden');
        
    } catch (error) {
        console.error("載入排行榜失敗:", error);
        document.getElementById('leaderboard-loading').innerHTML = 
            '<p class="text-red-500 text-center">載入失敗: ' + error.message + '</p>';
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-content').classList.remove('hidden');
    }
}

// ==================== 渲染排行榜 ====================

function renderLeaderboard(teams) {
    const leaderboardList = document.getElementById('leaderboard-list');
    leaderboardList.innerHTML = '';
    
    teams.forEach((team, index) => {
        const teamCard = createTeamCard(team, index);
        leaderboardList.appendChild(teamCard);
    });
}

function createTeamCard(team, index) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl border-2 border-gray-200 overflow-hidden hover:shadow-lg transition';
    
    // 前三名特殊樣式
    if (team.rank === 1) {
        card.className += ' border-yellow-400';
    } else if (team.rank === 2) {
        card.className += ' border-gray-400';
    } else if (team.rank === 3) {
        card.className += ' border-orange-400';
    }
    
    // 排名徽章
    let rankBadge = '';
    if (team.rank === 1) {
        rankBadge = '<div class="rank-badge rank-1">🥇</div>';
    } else if (team.rank === 2) {
        rankBadge = '<div class="rank-badge rank-2">🥈</div>';
    } else if (team.rank === 3) {
        rankBadge = '<div class="rank-badge rank-3">🥉</div>';
    } else {
        rankBadge = `<div class="rank-badge bg-gray-100 text-gray-600">${team.rank}</div>`;
    }
    
    card.innerHTML = `
        <div class="p-4 sm:p-6">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-4">
                    ${rankBadge}
                    <div>
                        <h3 class="text-xl font-bold text-gray-800">${escapeHtml(team.team_name)}</h3>
                        <p class="text-sm text-gray-500">
                            ${team.member_count} 位成員
                        </p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-3xl font-black text-yellow-600">${team.total_points}</p>
                    <p class="text-xs text-gray-500">團隊積分</p>
                </div>
            </div>
            
            <!-- 展開/收合按鈕 -->
            <button 
                onclick="toggleTeamDetails('${team.team_id}')" 
                class="w-full mt-2 py-2 text-sm text-blue-600 hover:text-blue-800 font-medium transition"
            >
                <span id="toggle-text-${team.team_id}">▼ 查看成員</span>
            </button>
            
            <!-- 成員清單（預設隱藏） -->
            <div id="members-${team.team_id}" class="hidden mt-4 pt-4 border-t border-gray-200">
                <div class="text-center py-4">
                    <div class="loading-spinner"></div>
                    <p class="text-gray-500 text-sm mt-2">載入成員中...</p>
                </div>
            </div>
        </div>
    `;
    
    return card;
}

// ==================== 展開/收合團隊詳情 ====================

async function toggleTeamDetails(teamId) {
    const membersDiv = document.getElementById(`members-${teamId}`);
    const toggleText = document.getElementById(`toggle-text-${teamId}`);
    
    if (expandedTeams.has(teamId)) {
        // 收合
        membersDiv.classList.add('hidden');
        toggleText.textContent = '▼ 查看成員';
        expandedTeams.delete(teamId);
    } else {
        // 展開
        membersDiv.classList.remove('hidden');
        toggleText.textContent = '▲ 收合';
        expandedTeams.add(teamId);
        
        // 如果尚未載入成員，則載入
        if (!membersDiv.dataset.loaded) {
            await loadTeamMembers(teamId);
            membersDiv.dataset.loaded = 'true';
        }
    }
}

async function loadTeamMembers(teamId) {
    const membersDiv = document.getElementById(`members-${teamId}`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/teams/${teamId}/members`);
        
        if (!response.ok) {
            throw new Error("無法取得成員清單");
        }
        
        const data = await response.json();
        const members = data.members;
        
        // 渲染成員清單
        membersDiv.innerHTML = '<h4 class="text-sm font-bold text-gray-700 mb-3">👥 團隊成員</h4>';
        
        if (members.length === 0) {
            membersDiv.innerHTML += '<p class="text-gray-500 text-sm text-center py-4">尚無成員</p>';
            return;
        }
        
        const membersList = document.createElement('div');
        membersList.className = 'space-y-2';
        
        members.forEach((member, index) => {
            const memberItem = document.createElement('div');
            memberItem.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
            
            const rankEmoji = index === 0 ? '🥇' : (index === 1 ? '🥈' : (index === 2 ? '🥉' : ''));
            const leaderBadge = member.is_leader ? '<span class="ml-2 text-xs bg-yellow-400 text-white px-2 py-0.5 rounded-full">👑 隊長</span>' : '';
            const mvpBadge = index === 0 ? '<span class="ml-2 text-xs bg-purple-500 text-white px-2 py-0.5 rounded-full">⭐ MVP</span>' : '';
            
            memberItem.innerHTML = `
                <div class="flex items-center space-x-3">
                    <span class="text-xl">${rankEmoji || '👤'}</span>
                    <div>
                        <p class="font-medium text-gray-800 text-sm">
                            成員 #${index + 1}
                            ${leaderBadge}
                            ${mvpBadge}
                        </p>
                        <p class="text-xs text-gray-500">
                            通報次數: ${member.report_count} 次
                        </p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-lg font-bold text-blue-600">${member.contribution_points}</p>
                    <p class="text-xs text-gray-500">貢獻積分</p>
                </div>
            `;
            
            membersList.appendChild(memberItem);
        });
        
        membersDiv.appendChild(membersList);
        
    } catch (error) {
        console.error("載入成員清單失敗:", error);
        membersDiv.innerHTML = '<p class="text-red-500 text-sm text-center py-4">載入失敗</p>';
    }
}

// ==================== 輔助函數 ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== 啟動 LIFF ====================

initializeLiff();
