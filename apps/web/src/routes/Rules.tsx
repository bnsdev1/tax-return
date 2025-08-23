import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle, XCircle, AlertTriangle, Info, RefreshCw } from 'lucide-react';

interface RuleResult {
  rule_code: string;
  description: string;
  input_values: Record<string, any>;
  output_values: Record<string, any>;
  passed: boolean;
  severity: 'error' | 'warning' | 'info';
  category: string;
  message: string;
}

interface RulesResponse {
  rules_applied: RuleResult[];
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
  warnings: number;
  errors: number;
  status: 'completed' | 'in_progress' | 'failed';
}

export function Rules() {
  const { returnId } = useParams<{ returnId: string }>();
  const [rulesData, setRulesData] = useState<RulesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [passedFilter, setPassedFilter] = useState('all');

  useEffect(() => {
    fetchRulesData();
  }, [returnId]);

  const fetchRulesData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/rules/${returnId}`);
      if (!response.ok) throw new Error('Failed to fetch rules data');
      const data = await response.json();
      setRulesData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load rules');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
      default:
        return <Info className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const filteredRules = rulesData?.rules_applied.filter(rule => {
    const matchesSearch = rule.description.toLowerCase().includes(searchFilter.toLowerCase()) ||
                         rule.rule_code.toLowerCase().includes(searchFilter.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || rule.category === categoryFilter;
    const matchesSeverity = severityFilter === 'all' || rule.severity === severityFilter;
    const matchesPassed = passedFilter === 'all' || 
                         (passedFilter === 'passed' && rule.passed) ||
                         (passedFilter === 'failed' && !rule.passed);
    
    return matchesSearch && matchesCategory && matchesSeverity && matchesPassed;
  }) || [];

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading rules validation...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-500" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">Rules Validation</h1>
          <button
            onClick={fetchRulesData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {rulesData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-gray-900">{rulesData.total_rules}</div>
              <div className="text-sm text-gray-600">Total Rules</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-green-600">{rulesData.passed_rules}</div>
              <div className="text-sm text-gray-600">Passed</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-red-600">{rulesData.failed_rules}</div>
              <div className="text-sm text-gray-600">Failed</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-yellow-600">{rulesData.warnings}</div>
              <div className="text-sm text-gray-600">Warnings</div>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search rules..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Categories</option>
              <option value="validation">Validation</option>
              <option value="computation">Computation</option>
              <option value="compliance">Compliance</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Severities</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={passedFilter}
              onChange={(e) => setPassedFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Rules List */}
      <div className="space-y-4">
        {filteredRules.map((rule, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg">
            <div className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  {rule.passed ? (
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  ) : (
                    getSeverityIcon(rule.severity)
                  )}
                  <div>
                    <h3 className="font-semibold text-gray-900">{rule.rule_code}</h3>
                    <p className="text-gray-600 mt-1">{rule.description}</p>
                    {rule.message && (
                      <p className="text-sm text-gray-500 mt-2">{rule.message}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(rule.severity)}`}>
                    {rule.severity.toUpperCase()}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    rule.passed 
                      ? 'bg-green-100 text-green-800 border border-green-200' 
                      : 'bg-red-100 text-red-800 border border-red-200'
                  }`}>
                    {rule.passed ? 'PASSED' : 'FAILED'}
                  </span>
                </div>
              </div>
              
              {(Object.keys(rule.input_values).length > 0 || Object.keys(rule.output_values).length > 0) && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.keys(rule.input_values).length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Input Values</h4>
                        <div className="bg-gray-50 p-3 rounded text-sm">
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(rule.input_values, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                    {Object.keys(rule.output_values).length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Output Values</h4>
                        <div className="bg-gray-50 p-3 rounded text-sm">
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(rule.output_values, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredRules.length === 0 && (
        <div className="text-center py-12">
          <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No rules found</h3>
          <p className="text-gray-600">Try adjusting your filters to see more results.</p>
        </div>
      )}
    </div>
  );
}