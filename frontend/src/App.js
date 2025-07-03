import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [crawlerData, setCrawlerData] = useState([]);
  const [crawlerStats, setCrawlerStats] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [crawlerStatus, setCrawlerStatus] = useState('stopped');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

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
              fetchCrawlerData();
              fetchCrawlerStats();
            }
          } catch (err) {
            console.error('处理WebSocket消息失败:', err);
          }
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket连接已关闭');
          setWsConnected(false);
          // 自动重连
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

  // 获取爬虫数据
  const fetchCrawlerData = async () => {
    try {
      const response = await axios.get(`${API}/crawler/data`);
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

  // 导出CSV
  const exportCsv = async () => {
    try {
      const response = await axios.get(`${API}/crawler/data/export`, {
        responseType: 'blob'
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
    fetchCrawlerData();
    fetchCrawlerStats();
    fetchAccounts();
    
    // 定期刷新数据
    const interval = setInterval(() => {
      fetchCrawlerData();
      fetchCrawlerStats();
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
              <h1 className="text-3xl font-bold text-gray-900">小八爬虫管理系统</h1>
              <div className="ml-4 flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {wsConnected ? '实时连接' : '连接断开'}
                </span>
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
                onClick={exportCsv}
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
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              数据面板
            </button>
            <button
              onClick={() => setActiveTab('accounts')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'accounts'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              账号管理
            </button>
          </nav>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
                          crawlerStats.crawl_status === 'running' ? 'bg-green-500' : 'bg-red-500'
                        }`}>
                          <span className="text-white font-bold">状</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">爬虫状态</dt>
                          <dd className="text-lg font-medium text-gray-900">
                            {crawlerStats.crawl_status === 'running' ? '运行中' : '已停止'}
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
                <h3 className="text-lg leading-6 font-medium text-gray-900">爬虫数据</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  最新爬取的数据记录，每50秒自动更新
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">账号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">序号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">命名</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">等级</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">门派</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">绝技</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">次数/总次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">总时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">运行时间</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {crawlerData.map((item, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.account_username}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.sequence_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.ip}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.level}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.guild}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.skill}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="font-medium text-blue-600">
                            {item.count_current}/{item.count_total}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.total_time}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            item.status === '在线' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.runtime}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {crawlerData.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-500">暂无数据</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'accounts' && (
          <div className="space-y-6">
            {/* 账号列表 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">账号管理</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  管理爬虫账号，查看状态和测试连接
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户名</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最后爬取时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">创建时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {accounts.map((account) => (
                      <tr key={account.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {account.username}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(account.status)}`}>
                            {account.status === 'active' ? '活跃' : account.status === 'inactive' ? '非活跃' : '错误'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatTime(account.last_crawl)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatTime(account.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => testAccount(account.username)}
                            disabled={loading}
                            className="text-blue-600 hover:text-blue-900 mr-4"
                          >
                            测试
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {accounts.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-500">暂无账号</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;