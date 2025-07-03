import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [crawlerData, setCrawlerData] = useState([]);
  const [crawlerStats, setCrawlerStats] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [keywordStats, setKeywordStats] = useState([]);
  const [dataSummary, setDataSummary] = useState(null);
  const [accountsPerformance, setAccountsPerformance] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [crawlerStatus, setCrawlerStatus] = useState('stopped');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // 新功能状态
  const [filters, setFilters] = useState({
    account_username: '',
    keyword: '',
    status: '',
    guild: '',
    min_count: '',
    max_count: ''
  });
  const [newAccount, setNewAccount] = useState({ username: '', password: '' });
  const [showAddAccount, setShowAddAccount] = useState(false);

  // WebSocket连接
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const wsUrl = `${BACKEND_URL.replace('http', 'ws')}/api/crawler/ws`;
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          console.log('WebSocket连接已建立');
          setWsConnected(true);
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'crawler_update') {
              console.log('收到实时更新:', data);
              fetchAllData();
            }
          } catch (err) {
            console.error('处理WebSocket消息失败:', err);
          }
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket连接已关闭');
          setWsConnected(false);
          setTimeout(connectWebSocket, 3000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket错误:', error);
          setWsConnected(false);
        };
      } catch (err) {
        console.error('WebSocket连接失败:', err);
        setWsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // 获取所有数据
  const fetchAllData = async () => {
    await Promise.all([
      fetchCrawlerData(),
      fetchCrawlerStats(),
      fetchAccounts(),
      fetchKeywordStats(),
      fetchDataSummary(),
      fetchAccountsPerformance()
    ]);
  };

  // 获取爬虫数据（带筛选）
  const fetchCrawlerData = async (customFilters = null) => {
    try {
      const params = {};
      const currentFilters = customFilters || filters;
      
      Object.keys(currentFilters).forEach(key => {
        if (currentFilters[key] && currentFilters[key] !== '') {
          params[key] = currentFilters[key];
        }
      });

      const response = await axios.get(`${API}/crawler/data`, { params });
      setCrawlerData(response.data);
    } catch (err) {
      console.error('获取爬虫数据失败:', err);
      setError('获取爬虫数据失败');
    }
  };

  // 获取爬虫统计信息
  const fetchCrawlerStats = async () => {
    try {
      const response = await axios.get(`${API}/crawler/status`);
      setCrawlerStats(response.data);
      setCrawlerStatus(response.data.crawl_status);
    } catch (err) {
      console.error('获取爬虫统计失败:', err);
      setError('获取爬虫统计失败');
    }
  };

  // 获取账号列表
  const fetchAccounts = async () => {
    try {
      const response = await axios.get(`${API}/crawler/accounts`);
      setAccounts(response.data);
    } catch (err) {
      console.error('获取账号列表失败:', err);
      setError('获取账号列表失败');
    }
  };

  // 获取关键词统计
  const fetchKeywordStats = async () => {
    try {
      const response = await axios.get(`${API}/crawler/data/keywords`);
      setKeywordStats(response.data);
    } catch (err) {
      console.error('获取关键词统计失败:', err);
    }
  };

  // 获取数据摘要
  const fetchDataSummary = async () => {
    try {
      const response = await axios.get(`${API}/crawler/data/summary`);
      setDataSummary(response.data);
    } catch (err) {
      console.error('获取数据摘要失败:', err);
    }
  };

  // 获取账号性能统计
  const fetchAccountsPerformance = async () => {
    try {
      const response = await axios.get(`${API}/crawler/data/accounts-performance`);
      setAccountsPerformance(response.data);
    } catch (err) {
      console.error('获取账号性能统计失败:', err);
    }
  };

  // 启动爬虫
  const startCrawler = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/crawler/start`);
      setCrawlerStatus('running');
      setError(null);
      await fetchCrawlerStats();
    } catch (err) {
      console.error('启动爬虫失败:', err);
      setError('启动爬虫失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 停止爬虫
  const stopCrawler = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/crawler/stop`);
      setCrawlerStatus('stopped');
      setError(null);
      await fetchCrawlerStats();
    } catch (err) {
      console.error('停止爬虫失败:', err);
      setError('停止爬虫失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 批量启用所有账号
  const enableAllAccounts = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/crawler/accounts/batch/enable`);
      setError(null);
      await fetchAccounts();
      alert('已启用所有账号');
    } catch (err) {
      console.error('批量启用账号失败:', err);
      setError('批量启用账号失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 批量禁用所有账号
  const disableAllAccounts = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/crawler/accounts/batch/disable`);
      setError(null);
      await fetchAccounts();
      alert('已禁用所有账号');
    } catch (err) {
      console.error('批量禁用账号失败:', err);
      setError('批量禁用账号失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 启用/禁用单个账号
  const toggleAccount = async (username, currentStatus) => {
    setLoading(true);
    try {
      const action = currentStatus === 'disabled' ? 'enable' : 'disable';
      await axios.post(`${API}/crawler/accounts/${username}/${action}`);
      setError(null);
      await fetchAccounts();
    } catch (err) {
      console.error(`${action}账号失败:`, err);
      setError(`${action}账号失败: ` + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 添加账号
  const addAccount = async () => {
    if (!newAccount.username || !newAccount.password) {
      setError('请填写完整的账号信息');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/crawler/accounts/validate`, newAccount);
      setError(null);
      setNewAccount({ username: '', password: '' });
      setShowAddAccount(false);
      await fetchAccounts();
      alert('账号添加成功！');
    } catch (err) {
      console.error('添加账号失败:', err);
      setError('添加账号失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 删除账号
  const deleteAccount = async (username) => {
    if (!confirm(`确定要删除账号 ${username} 吗？`)) return;

    setLoading(true);
    try {
      await axios.delete(`${API}/crawler/accounts/${username}`);
      setError(null);
      await fetchAccounts();
      alert('账号删除成功！');
    } catch (err) {
      console.error('删除账号失败:', err);
      setError('删除账号失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 测试账号
  const testAccount = async (username) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/crawler/test/${username}`);
      alert(`测试结果: ${response.data.test_result === 'success' ? '成功' : '失败'}`);
      await fetchAccounts();
    } catch (err) {
      console.error('测试账号失败:', err);
      setError('测试账号失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 应用筛选
  const applyFilters = () => {
    fetchCrawlerData();
  };

  // 清除筛选
  const clearFilters = () => {
    setFilters({
      account_username: '',
      keyword: '',
      status: '',
      guild: '',
      min_count: '',
      max_count: ''
    });
    fetchCrawlerData({});
  };

  // 导出CSV
  const exportCsv = async (includeKeywords = true, includeAccumulated = true) => {
    try {
      const params = {
        include_keywords: includeKeywords,
        include_accumulated: includeAccumulated
      };

      const response = await axios.get(`${API}/crawler/data/export`, {
        responseType: 'blob',
        params
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'crawler_data.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('导出CSV失败:', err);
      setError('导出CSV失败');
    }
  };

  // 页面加载时获取数据
  useEffect(() => {
    fetchAllData();
    
    // 定期刷新数据
    const interval = setInterval(() => {
      fetchAllData();
    }, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, []);

  // 格式化时间
  const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString('zh-CN');
  };

  // 获取状态样式
  const getStatusStyle = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'disabled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 头部 */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">小八爬虫管理系统 v2.0</h1>
              <div className="ml-4 flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {wsConnected ? '实时连接' : '连接断开'}
                </span>
              </div>
              <div className="ml-4 text-sm text-gray-600">
                刷新间隔: 45秒 | 状态: {crawlerStatus === 'running' ? '运行中' : '已停止'}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={crawlerStatus === 'running' ? stopCrawler : startCrawler}
                disabled={loading}
                className={`px-4 py-2 rounded-md font-medium ${
                  crawlerStatus === 'running'
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? '处理中...' : crawlerStatus === 'running' ? '停止爬虫' : '启动爬虫'}
              </button>
              <button
                onClick={() => exportCsv()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                导出CSV
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
            <button
              onClick={() => setError(null)}
              className="float-right font-bold text-red-700 hover:text-red-900"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* 标签页 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['dashboard', 'data', 'accounts', 'analytics', 'keywords'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab === 'dashboard' && '数据面板'}
                {tab === 'data' && '数据筛选'}
                {tab === 'accounts' && '账号管理'}
                {tab === 'analytics' && '统计分析'}
                {tab === 'keywords' && '关键词统计'}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 数据面板 */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* 统计卡片 */}
            {crawlerStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">总</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">总账号数</dt>
                          <dd className="text-lg font-medium text-gray-900">{crawlerStats.total_accounts}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">活</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">活跃账号</dt>
                          <dd className="text-lg font-medium text-gray-900">{crawlerStats.active_accounts}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">记</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">总记录数</dt>
                          <dd className="text-lg font-medium text-gray-900">{crawlerStats.total_records}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          crawlerStatus === 'running' ? 'bg-green-500' : 'bg-red-500'
                        }`}>
                          <span className="text-white font-bold">状</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">爬虫状态</dt>
                          <dd className="text-lg font-medium text-gray-900">
                            {crawlerStatus === 'running' ? '运行中' : '已停止'}
                          </dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 数据表格 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">最新爬虫数据</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">显示最近的爬虫数据记录</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">账号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">序号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">名称</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">等级</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">门派</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">绝技</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">次数/总数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">累计次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">爬取时间</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {crawlerData.slice(0, 20).map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.account_username}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.sequence_number}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.ip}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.type}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.level}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.guild}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.skill}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.count_current}/{item.count_total}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-bold text-blue-600">{item.accumulated_count || 0}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusStyle(item.status)}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatTime(item.crawl_timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 数据筛选 */}
        {activeTab === 'data' && (
          <div className="space-y-6">
            {/* 筛选条件 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">数据筛选</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">使用以下条件筛选爬虫数据</p>
              </div>
              <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">账号</label>
                    <input
                      type="text"
                      value={filters.account_username}
                      onChange={(e) => setFilters({...filters, account_username: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                      placeholder="输入账号名称"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">关键词</label>
                    <input
                      type="text"
                      value={filters.keyword}
                      onChange={(e) => setFilters({...filters, keyword: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                      placeholder="搜索关键词"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">状态</label>
                    <select
                      value={filters.status}
                      onChange={(e) => setFilters({...filters, status: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                    >
                      <option value="">全部状态</option>
                      <option value="在线">在线</option>
                      <option value="离线">离线</option>
                      <option value="忙碌">忙碌</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">门派</label>
                    <input
                      type="text"
                      value={filters.guild}
                      onChange={(e) => setFilters({...filters, guild: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                      placeholder="输入门派名称"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">最小次数</label>
                    <input
                      type="number"
                      value={filters.min_count}
                      onChange={(e) => setFilters({...filters, min_count: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                      placeholder="最小次数"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">最大次数</label>
                    <input
                      type="number"
                      value={filters.max_count}
                      onChange={(e) => setFilters({...filters, max_count: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                      placeholder="最大次数"
                    />
                  </div>
                </div>
                <div className="mt-4 flex space-x-4">
                  <button
                    onClick={applyFilters}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                  >
                    应用筛选
                  </button>
                  <button
                    onClick={clearFilters}
                    className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
                  >
                    清除筛选
                  </button>
                  <button
                    onClick={() => exportCsv(true, true)}
                    className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
                  >
                    导出筛选结果
                  </button>
                </div>
              </div>
            </div>

            {/* 筛选结果 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">筛选结果 ({crawlerData.length} 条记录)</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">账号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">序号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">名称</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">等级</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">门派</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">绝技</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">次数/总数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">累计次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">关键词</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">爬取时间</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {crawlerData.map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.account_username}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.sequence_number}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.ip}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.type}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.level}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.guild}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.skill}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.count_current}/{item.count_total}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-bold text-blue-600">{item.accumulated_count || 0}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.keywords_detected && Object.keys(item.keywords_detected).length > 0 ? (
                            <div className="space-y-1">
                              {Object.entries(item.keywords_detected).map(([keyword, count]) => (
                                <span key={keyword} className="inline-block bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full mr-1">
                                  {keyword}: {count}
                                </span>
                              ))}
                            </div>
                          ) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusStyle(item.status)}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatTime(item.crawl_timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 账号管理 */}
        {activeTab === 'accounts' && (
          <div className="space-y-6">
            {/* 批量操作 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">批量操作</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">批量管理所有账号</p>
              </div>
              <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                <div className="flex space-x-4">
                  <button
                    onClick={enableAllAccounts}
                    disabled={loading}
                    className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    启用所有账号
                  </button>
                  <button
                    onClick={disableAllAccounts}
                    disabled={loading}
                    className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
                  >
                    禁用所有账号
                  </button>
                  <button
                    onClick={() => setShowAddAccount(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                  >
                    添加账号
                  </button>
                </div>
              </div>
            </div>

            {/* 添加账号模态框 */}
            {showAddAccount && (
              <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                  <div className="mt-3">
                    <h3 className="text-lg font-medium text-gray-900">添加新账号</h3>
                    <div className="mt-4 space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">用户名</label>
                        <input
                          type="text"
                          value={newAccount.username}
                          onChange={(e) => setNewAccount({...newAccount, username: e.target.value})}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                          placeholder="输入用户名"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">密码</label>
                        <input
                          type="password"
                          value={newAccount.password}
                          onChange={(e) => setNewAccount({...newAccount, password: e.target.value})}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                          placeholder="输入密码"
                        />
                      </div>
                      <div className="flex justify-end space-x-4">
                        <button
                          onClick={() => {
                            setShowAddAccount(false);
                            setNewAccount({ username: '', password: '' });
                          }}
                          className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                        >
                          取消
                        </button>
                        <button
                          onClick={addAccount}
                          disabled={loading}
                          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                        >
                          {loading ? '验证中...' : '添加账号'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 账号列表 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">账号列表 ({accounts.length} 个账号)</h3>
              </div>
              <ul className="divide-y divide-gray-200">
                {accounts.map((account) => (
                  <li key={account.username}>
                    <div className="px-4 py-4 flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                            <span className="text-sm font-medium text-gray-700">{account.username.slice(0, 2)}</span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{account.username}</div>
                          <div className="text-sm text-gray-500">
                            状态: <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusStyle(account.status)}`}>
                              {account.status}
                            </span>
                          </div>
                          <div className="text-sm text-gray-500">
                            最后爬取: {formatTime(account.last_crawl)}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => toggleAccount(account.username, account.status)}
                          disabled={loading}
                          className={`px-3 py-1 rounded text-sm font-medium ${
                            account.status === 'disabled'
                              ? 'bg-green-100 text-green-800 hover:bg-green-200'
                              : 'bg-red-100 text-red-800 hover:bg-red-200'
                          } disabled:opacity-50`}
                        >
                          {account.status === 'disabled' ? '启用' : '禁用'}
                        </button>
                        <button
                          onClick={() => testAccount(account.username)}
                          disabled={loading}
                          className="bg-blue-100 text-blue-800 px-3 py-1 rounded text-sm font-medium hover:bg-blue-200 disabled:opacity-50"
                        >
                          测试
                        </button>
                        <button
                          onClick={() => deleteAccount(account.username)}
                          disabled={loading}
                          className="bg-red-100 text-red-800 px-3 py-1 rounded text-sm font-medium hover:bg-red-200 disabled:opacity-50"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 统计分析 */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {/* 数据摘要 */}
            {dataSummary && (
              <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">数据摘要</h3>
                </div>
                <div className="border-t border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{dataSummary.total_records}</div>
                      <div className="text-sm text-gray-500">总记录数</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{dataSummary.recent_records_24h}</div>
                      <div className="text-sm text-gray-500">24小时内记录</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{dataSummary.accumulation_stats?.total_accumulated || 0}</div>
                      <div className="text-sm text-gray-500">总累计次数</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{Math.round(dataSummary.accumulation_stats?.avg_accumulated || 0)}</div>
                      <div className="text-sm text-gray-500">平均累计次数</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 账号性能统计 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">账号性能统计</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">账号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">总记录数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">累计次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">当前总次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">平均次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">关键词检测</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最后爬取</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {accountsPerformance.map((account, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{account._id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{account.total_records}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-bold text-blue-600">{account.total_accumulated}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{account.total_current}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(account.avg_current)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{account.keywords_detected}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatTime(account.last_crawl)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 关键词统计 */}
        {activeTab === 'keywords' && (
          <div className="space-y-6">
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">关键词统计</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">追踪关键词如"人脸提示"、"没钱了"等在数据中的出现情况</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">关键词</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">总次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">影响账号数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">影响账号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最后发现</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {keywordStats.map((keyword, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                            {keyword.keyword}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-bold text-red-600">{keyword.total_count}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{keyword.accounts_affected?.length || 0}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {keyword.accounts_affected?.slice(0, 3).join(', ')}
                          {keyword.accounts_affected?.length > 3 && ` +${keyword.accounts_affected.length - 3}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatTime(keyword.last_seen)}</td>
                      </tr>
                    ))}
                    {keywordStats.length === 0 && (
                      <tr>
                        <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                          暂无关键词统计数据
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;