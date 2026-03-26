// team.js - 團隊管理頁面 JavaScript

// ⚠️ 重要：請將這些 LIFF ID 替換為你在 LINE Developers Console 建立的 LIFF ID
const LIFF_ID_TEAM_MANAGEMENT = "2009609029-RlBZuNs2"; // 團隊管理頁面 LIFF ID
const API_BASE_URL = window.location.origin;

// 全域變數
let currentUser = null;
let currentTeam = null;
let isLeader = false;
let joinTeamId = null;
let joinSignature = null;

// ==================== LIFF 初始化 ====================

async function initializeLiff() {
    try {
        console.log("正在初始化 LIFF...");
        await liff.init({ liffId: LIFF_ID_TEAM_MANAGEMENT });
        
        console.log("LIFF 初始化成功");
        console.log("登入狀態:", liff.isLoggedIn());
        
        if (!liff.isLoggedIn()) {
            console.log("使用者未登入，導向登入頁面");
            liff.login();
        } else {
            console.log("使用者已登入，載入頁面");
            await loadPage();
        }
    } catch (error) {
        console.error("LIFF 初始化失敗:", error);
        showError("LIFF 初始化失敗: " + error.message);
    }
}

// ==================== 頁面載入 ====================

async function loadPage() {
    try {
        // 取得使用者資料
        const profile = await liff.getProfile();
        currentUser = profile;
        console.log("使用者資料:", profile);
        
        // 顯示使用者資訊
        document.getElementById('user-avatar').src = profile.pictureUrl || 'https://via.placeholder.com/48';
        document.getElementById('user-name').textContent = profile.displayName;
        
        // 解析 URL 參數（檢查是否為邀請連結）
        console.log("=== URL 參數解析開始 ===");
        console.log("完整 URL:", window.location.href);
        console.log("URL 參數:", window.location.search);
        console.log("LIFF context:", liff.getContext());
        
        // 優先從 window.location.search 讀取參數
        let urlParams = new URLSearchParams(window.location.search);
        joinTeamId = urlParams.get('team_id');
        joinSignature = urlParams.get('signature');
        
        console.log("從 URL 讀取 - team_id:", joinTeamId);
        console.log("從 URL 讀取 - signature:", joinSignature);
        
        // 如果沒有參數，嘗試從 liff.state 讀取
        if (!joinTeamId || !joinSignature) {
            const context = liff.getContext();
            console.log("嘗試從 liff.state 讀取參數");
            console.log("Context:", context);
            
            if (context && context.liffState) {
                const liffState = context.liffState;
                console.log("liff.state 原始值:", liffState);
                
                // liffState 可能是 URL encoded，需要 decode
                const decodedState = decodeURIComponent(liffState);
                console.log("liff.state 解碼後:", decodedState);
                
                // liffState 格式: /team.html?team_id=xxx&signature=xxx
                if (decodedState.includes('?')) {
                    const stateParams = new URLSearchParams(decodedState.split('?')[1]);
                    joinTeamId = stateParams.get('team_id');
                    joinSignature = stateParams.get('signature');
                    
                    console.log("從 liff.state 讀取 - team_id:", joinTeamId);
                    console.log("從 liff.state 讀取 - signature:", joinSignature);
                }
            } else {
                console.log("liff.state 不存在");
            }
        }
        
        console.log("=== 最終解析結果 ===");
        console.log("team_id:", joinTeamId);
        console.log("signature:", joinSignature);
        
        if (joinTeamId && joinSignature) {
            // 邀請連結模式
            console.log("✅ 檢測到邀請連結，進入加入團隊模式");
            await loadJoinTeamMode();
        } else {
            // 一般模式：檢查使用者是否已有團隊
            console.log("ℹ️ 未檢測到邀請參數，進入團隊管理模式");
            await loadTeamManagementMode();
        }
        
        // 隱藏 loading，顯示主要內容
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-content').classList.remove('hidden');
        
    } catch (error) {
        console.error("載入頁面失敗:", error);
        showError("載入頁面失敗: " + error.message);
    }
}

// ==================== 團隊管理模式 ====================

async function loadTeamManagementMode() {
    try {
        // 查詢使用者所屬團隊
        const teamInfo = await getUserTeam(currentUser.userId);
        
        if (teamInfo) {
            // 使用者已有團隊
            currentTeam = teamInfo;
            isLeader = (teamInfo.leader_uid === currentUser.userId);
            
            document.getElementById('user-status').textContent = isLeader ? '👑 隊長' : '👤 隊員';
            
            // 顯示團隊資訊區塊
            document.getElementById('team-info-section').classList.remove('hidden');
            await loadTeamInfo();
            await loadTeamMembers();
            
            // 如果是隊長，顯示邀請按鈕
            if (isLeader) {
                document.getElementById('invite-btn').classList.remove('hidden');
            }
        } else {
            // 使用者尚未建立或加入團隊
            document.getElementById('user-status').textContent = '尚未加入團隊';
            document.getElementById('create-team-section').classList.remove('hidden');
            
            // 監聽團隊名稱輸入
            const teamNameInput = document.getElementById('team-name-input');
            teamNameInput.addEventListener('input', function() {
                const charCount = this.value.length;
                document.getElementById('char-count').textContent = charCount;
                
                // 啟用/停用建立按鈕
                const createBtn = document.getElementById('create-team-btn');
                if (charCount > 0 && charCount <= 30) {
                    createBtn.disabled = false;
                    createBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                } else {
                    createBtn.disabled = true;
                    createBtn.classList.add('opacity-50', 'cursor-not-allowed');
                }
            });
        }
    } catch (error) {
        console.error("載入團隊管理模式失敗:", error);
        showToast("載入失敗: " + error.message, 'error');
    }
}

// ==================== 加入團隊模式 ====================

async function loadJoinTeamMode() {
    try {
        // 查詢目標團隊資訊
        const response = await fetch(`${API_BASE_URL}/api/teams/${joinTeamId}`);
        
        if (!response.ok) {
            throw new Error("團隊不存在或已解散");
        }
        
        const teamData = await response.json();
        
        // 顯示團隊資訊
        document.getElementById('join-team-name').textContent = teamData.team_name;
        document.getElementById('join-member-count').textContent = teamData.member_count;
        
        // 顯示加入團隊區塊
        document.getElementById('user-status').textContent = '收到團隊邀請';
        document.getElementById('join-team-section').classList.remove('hidden');
        
    } catch (error) {
        console.error("載入加入團隊模式失敗:", error);
        showError("無法載入團隊資訊: " + error.message);
    }
}

// ==================== API 呼叫函數 ====================

async function getUserTeam(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}/team`);
        
        if (!response.ok) {
            throw new Error("無法查詢使用者團隊");
        }
        
        const data = await response.json();
        
        if (data.has_team) {
            return {
                team_id: data.team_id,
                team_name: data.team_name,
                leader_uid: data.is_leader ? userId : null,
                is_leader: data.is_leader
            };
        }
        
        return null;
    } catch (error) {
        console.error("查詢使用者團隊失敗:", error);
        return null;
    }
}

async function loadTeamInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/teams/${currentTeam.team_id}`);
        
        if (!response.ok) {
            throw new Error("無法取得團隊資訊");
        }
        
        const teamData = await response.json();
        
        // 更新團隊資訊顯示
        document.getElementById('team-name').textContent = teamData.team_name;
        document.getElementById('team-points').textContent = teamData.total_points;
        document.getElementById('member-count').textContent = teamData.member_count;
        
        // 取得隊長名稱（需要從成員清單中查詢）
        // 暫時顯示 "隊長"
        document.getElementById('team-leader-name').textContent = isLeader ? currentUser.displayName : "隊長";
        
    } catch (error) {
        console.error("載入團隊資訊失敗:", error);
        showToast("載入團隊資訊失敗", 'error');
    }
}

async function loadTeamMembers() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/teams/${currentTeam.team_id}/members`);
        
        if (!response.ok) {
            throw new Error("無法取得成員清單");
        }
        
        const data = await response.json();
        const members = data.members;
        
        // 隱藏 loading
        document.getElementById('members-loading').classList.add('hidden');
        document.getElementById('members-list').classList.remove('hidden');
        
        // 渲染成員清單
        const membersList = document.getElementById('members-list');
        membersList.innerHTML = '';
        
        // 計算我的貢獻
        let myContribution = 0;
        
        members.forEach((member, index) => {
            if (member.line_uid === currentUser.userId) {
                myContribution = member.contribution_points;
            }
            
            const memberDiv = document.createElement('div');
            memberDiv.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition';
            
            const rankEmoji = index === 0 ? '🥇' : (index === 1 ? '🥈' : (index === 2 ? '🥉' : ''));
            const leaderBadge = member.is_leader ? '<span class="ml-2 text-xs bg-yellow-400 text-white px-2 py-0.5 rounded-full">👑 隊長</span>' : '';
            const meBadge = member.line_uid === currentUser.userId ? '<span class="ml-2 text-xs bg-blue-400 text-white px-2 py-0.5 rounded-full">我</span>' : '';
            
            memberDiv.innerHTML = `
                <div class="flex items-center space-x-3">
                    <span class="text-2xl">${rankEmoji || '👤'}</span>
                    <div>
                        <p class="font-medium text-gray-800">
                            成員 #${index + 1}
                            ${leaderBadge}
                            ${meBadge}
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
            
            membersList.appendChild(memberDiv);
        });
        
        // 更新我的貢獻顯示
        document.getElementById('my-contribution').textContent = myContribution;
        
    } catch (error) {
        console.error("載入成員清單失敗:", error);
        document.getElementById('members-loading').innerHTML = 
            '<p class="text-red-500 text-center">載入失敗</p>';
    }
}

// ==================== 團隊操作函數 ====================

async function createTeam() {
    const teamNameInput = document.getElementById('team-name-input');
    const teamName = teamNameInput.value.trim();
    
    if (!teamName || teamName.length > 30) {
        showToast('請輸入有效的團隊名稱（1-30 字元）', 'error');
        return;
    }
    
    const createBtn = document.getElementById('create-team-btn');
    createBtn.disabled = true;
    createBtn.textContent = '建立中...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/teams/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                leader_uid: currentUser.userId,
                team_name: teamName
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '建立團隊失敗');
        }
        
        const data = await response.json();
        console.log("團隊建立成功:", data);
        
        showToast('🎉 團隊建立成功！', 'success');
        
        // 重新載入頁面
        setTimeout(() => {
            window.location.reload();
        }, 1500);
        
    } catch (error) {
        console.error("建立團隊失敗:", error);
        showToast('建立失敗: ' + error.message, 'error');
        createBtn.disabled = false;
        createBtn.textContent = '✨ 建立團隊';
    }
}

async function confirmJoinTeam() {
    alert("confirmJoinTeam 函數被呼叫了！"); // 測試用
    console.log("=== 開始加入團隊流程 ===");
    console.log("Team ID:", joinTeamId);
    console.log("Signature:", joinSignature);
    console.log("User ID:", currentUser ? currentUser.userId : "currentUser is null");
    
    const joinBtn = document.getElementById('join-team-btn');
    if (!joinBtn) {
        console.error("找不到 join-team-btn 按鈕！");
        alert("錯誤：找不到按鈕元素");
        return;
    }
    
    joinBtn.disabled = true;
    joinBtn.textContent = '加入中...';
    
    try {
        const requestBody = {
            team_id: joinTeamId,
            member_uid: currentUser.userId,
            signature: joinSignature
        };
        
        console.log("發送加入團隊請求:", requestBody);
        
        const response = await fetch(`${API_BASE_URL}/api/teams/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log("API 回應狀態:", response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error("API 錯誤:", errorData);
            throw new Error(errorData.detail || '加入團隊失敗');
        }
        
        const data = await response.json();
        console.log("加入團隊成功:", data);
        
        showToast('🎉 成功加入團隊！', 'success');
        
        // 移除 URL 參數並重新載入
        setTimeout(() => {
            window.location.href = 'team.html';
        }, 1500);
        
    } catch (error) {
        console.error("加入團隊失敗:", error);
        showToast('加入失敗: ' + error.message, 'error');
        joinBtn.disabled = false;
        joinBtn.textContent = '✅ 確認加入團隊';
    }
}

async function inviteMembers() {
    try {
        console.log("開始邀請流程...");
        console.log("LIFF 登入狀態:", liff.isLoggedIn());
        console.log("在 LINE 內開啟:", liff.isInClient());
        console.log("ShareTargetPicker 可用:", liff.isApiAvailable('shareTargetPicker'));
        
        console.log("正在產生邀請 URL...");
        // 產生邀請 URL
        const inviteUrl = await getInviteUrl(currentTeam.team_id);
        console.log("邀請 URL:", inviteUrl);
        
        // 取得完整的團隊資訊（包含 member_count 和 total_points）
        const response = await fetch(`${API_BASE_URL}/api/teams/${currentTeam.team_id}`);
        if (!response.ok) {
            throw new Error("無法取得團隊資訊");
        }
        const fullTeamInfo = await response.json();
        console.log("完整團隊資訊:", fullTeamInfo);
        
        // 檢查是否在 LINE 內開啟且 ShareTargetPicker 可用
        if (liff.isInClient() && liff.isApiAvailable('shareTargetPicker')) {
            console.log("使用 ShareTargetPicker 發送邀請");
            
            // 建立 Flex Message 邀請卡片（使用完整團隊資訊）
            const flexMessage = createInviteFlexMessage(fullTeamInfo, inviteUrl);
            console.log("Flex Message 已建立");
            
            // 開啟 ShareTargetPicker
            console.log("開啟 ShareTargetPicker...");
            const result = await liff.shareTargetPicker([flexMessage]);
            
            if (result) {
                console.log("邀請訊息發送成功");
                showToast('📨 邀請已發送！', 'success');
            }
        } else {
            console.log("ShareTargetPicker 不可用或不在 LINE 內，使用備用方案");
            
            // 備用方案：顯示邀請連結讓使用者複製
            showInviteLinkDialog(inviteUrl);
        }
        
    } catch (error) {
        console.error("發送邀請失敗:", error);
        if (error.message === 'CANCEL') {
            console.log("使用者取消發送");
        } else {
            showToast('發送邀請失敗: ' + error.message, 'error');
        }
    }
}

function showInviteLinkDialog(inviteUrl) {
    // 建立對話框顯示邀請連結
    const dialog = document.createElement('div');
    dialog.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    dialog.innerHTML = `
        <div class="bg-white rounded-xl p-6 max-w-md w-full">
            <h3 class="text-lg font-bold text-gray-800 mb-4">📨 邀請好友加入</h3>
            <p class="text-sm text-gray-600 mb-4">複製下方連結並分享給好友：</p>
            
            <div class="bg-gray-100 rounded-lg p-3 mb-4 break-all text-sm">
                ${inviteUrl}
            </div>
            
            <div class="flex space-x-3">
                <button 
                    onclick="copyInviteLink('${inviteUrl}')" 
                    class="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg transition"
                >
                    📋 複製連結
                </button>
                <button 
                    onclick="closeInviteDialog()" 
                    class="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg transition"
                >
                    關閉
                </button>
            </div>
        </div>
    `;
    
    dialog.id = 'invite-dialog';
    document.body.appendChild(dialog);
}

function copyInviteLink(url) {
    // 複製連結到剪貼簿
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
            showToast('✅ 連結已複製！', 'success');
            closeInviteDialog();
        }).catch(err => {
            console.error('複製失敗:', err);
            showToast('複製失敗，請手動複製', 'error');
        });
    } else {
        // 備用方案：使用舊的 execCommand
        const textArea = document.createElement('textarea');
        textArea.value = url;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('✅ 連結已複製！', 'success');
            closeInviteDialog();
        } catch (err) {
            console.error('複製失敗:', err);
            showToast('複製失敗，請手動複製', 'error');
        }
        document.body.removeChild(textArea);
    }
}

function closeInviteDialog() {
    const dialog = document.getElementById('invite-dialog');
    if (dialog) {
        dialog.remove();
    }
}

async function getInviteUrl(teamId) {
    try {
        const url = `${API_BASE_URL}/api/teams/${teamId}/invite?inviter_uid=${currentUser.userId}`;
        console.log("正在呼叫邀請 API:", url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error("無法產生邀請連結");
        }
        
        const data = await response.json();
        console.log("邀請 API 回應:", data);
        console.log("邀請 URL:", data.invite_url);
        
        return data.invite_url;
    } catch (error) {
        console.error("產生邀請連結失敗:", error);
        throw error;
    }
}

function createInviteFlexMessage(team, inviteUrl) {
    return {
        type: 'flex',
        altText: `${team.team_name} 邀請您加入團隊！`,
        contents: {
            type: 'bubble',
            hero: {
                type: 'box',
                layout: 'vertical',
                contents: [
                    {
                        type: 'text',
                        text: '🏆 團隊邀請',
                        weight: 'bold',
                        size: 'xl',
                        color: '#ffffff'
                    }
                ],
                backgroundColor: '#3b82f6',
                paddingAll: '20px'
            },
            body: {
                type: 'box',
                layout: 'vertical',
                contents: [
                    {
                        type: 'text',
                        text: team.team_name,
                        weight: 'bold',
                        size: 'xxl',
                        wrap: true
                    },
                    {
                        type: 'box',
                        layout: 'vertical',
                        margin: 'lg',
                        spacing: 'sm',
                        contents: [
                            {
                                type: 'box',
                                layout: 'baseline',
                                spacing: 'sm',
                                contents: [
                                    {
                                        type: 'text',
                                        text: '隊長',
                                        color: '#aaaaaa',
                                        size: 'sm',
                                        flex: 1
                                    },
                                    {
                                        type: 'text',
                                        text: currentUser.displayName,
                                        wrap: true,
                                        color: '#666666',
                                        size: 'sm',
                                        flex: 3
                                    }
                                ]
                            },
                            {
                                type: 'box',
                                layout: 'baseline',
                                spacing: 'sm',
                                contents: [
                                    {
                                        type: 'text',
                                        text: '成員數',
                                        color: '#aaaaaa',
                                        size: 'sm',
                                        flex: 1
                                    },
                                    {
                                        type: 'text',
                                        text: `${team.member_count} 人`,
                                        wrap: true,
                                        color: '#666666',
                                        size: 'sm',
                                        flex: 3
                                    }
                                ]
                            },
                            {
                                type: 'box',
                                layout: 'baseline',
                                spacing: 'sm',
                                contents: [
                                    {
                                        type: 'text',
                                        text: '團隊積分',
                                        color: '#aaaaaa',
                                        size: 'sm',
                                        flex: 1
                                    },
                                    {
                                        type: 'text',
                                        text: `${team.total_points} 分`,
                                        wrap: true,
                                        color: '#666666',
                                        size: 'sm',
                                        flex: 3
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        type: 'text',
                        text: '一起通報詐騙，累積團隊積分！',
                        wrap: true,
                        color: '#999999',
                        size: 'xs',
                        margin: 'md'
                    }
                ]
            },
            footer: {
                type: 'box',
                layout: 'vertical',
                spacing: 'sm',
                contents: [
                    {
                        type: 'button',
                        style: 'primary',
                        height: 'sm',
                        action: {
                            type: 'uri',
                            label: '✅ 加入團隊',
                            uri: inviteUrl
                        }
                    }
                ],
                flex: 0
            }
        }
    };
}

// ==================== 輔助函數 ====================

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    
    toastMessage.textContent = message;
    toast.classList.remove('hidden', 'bg-gray-800', 'bg-green-600', 'bg-red-600');
    
    if (type === 'success') {
        toast.classList.add('bg-green-600');
    } else if (type === 'error') {
        toast.classList.add('bg-red-600');
    } else {
        toast.classList.add('bg-gray-800');
    }
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function showError(message) {
    document.getElementById('loading-screen').classList.add('hidden');
    document.getElementById('error-screen').classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
}

// ==================== 啟動 LIFF ====================

initializeLiff();
