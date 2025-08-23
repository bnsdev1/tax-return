import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Badge,
  LinearProgress
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Clear as ClearIcon
} from '@mui/icons-material';

interface RuleResult {
  rule_code: string;
  description: string;
  input_values: Record<string, any>;
  output_value: any;
  passed: boolean;
  message: string;
  severity: 'info' | 'warning' | 'error';
  timestamp: string;
}

interface RuleSummary {
  total_rules: number;
  passed: number;
  failed: number;
  errors: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
}

interface RuleDefinition {
  code: string;
  description: string;
  expression: string;
  severity: 'info' | 'warning' | 'error';
  message_pass: string;
  message_fail: string;
  enabled: boolean;
  category: string;
}

const Rules: React.FC = () => {
  const [rulesLog, setRulesLog] = useState<RuleResult[]>([]);
  const [ruleDefinitions, setRuleDefinitions] = useState<RuleDefinition[]>([]);
  const [summary, setSummary] = useState<RuleSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [passedFilter, setPassedFilter] = useState<string>('');
  const [searchFilter, setSearchFilter] = useState<string>('');
  
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage] = useState(50);
  
  // Available filter options
  const categories = ['deductions', 'income', 'tax', 'rebate', 'capital_gains', 'house_property', 'tds', 'refund', 'age'];
  const severities = ['info', 'warning', 'error'];

  useEffect(() => {
    fetchRulesData();
    fetchRuleDefinitions();
  }, []);

  const fetchRulesData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (severityFilter) params.append('severity', severityFilter);
      if (passedFilter) params.append('passed', passedFilter);
      params.append('limit', rowsPerPage.toString());
      params.append('offset', (page * rowsPerPage).toString());
      
      const response = await fetch(`/api/rules/log?${params}`);
      if (!response.ok) throw new Error('Failed to fetch rules log');
      
      const data = await response.json();
      setRulesLog(data.results);
      setSummary(data.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchRuleDefinitions = async () => {
    try {
      const response = await fetch('/api/rules/definitions');
      if (!response.ok) throw new Error('Failed to fetch rule definitions');
      
      const data = await response.json();
      setRuleDefinitions(data.rules);
    } catch (err) {
      console.error('Failed to fetch rule definitions:', err);
    }
  };

  const clearRulesLog = async () => {
    try {
      const response = await fetch('/api/rules/clear-log', { method: 'POST' });
      if (!response.ok) throw new Error('Failed to clear rules log');
      
      await fetchRulesData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity: string): "error" | "warning" | "info" => {
    switch (severity) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
      default:
        return 'info';
    }
  };

  const getPassedIcon = (passed: boolean) => {
    return passed ? 
      <CheckCircleIcon color="success" /> : 
      <ErrorIcon color="error" />;
  };

  const filteredRules = rulesLog.filter(rule => {
    if (searchFilter && !rule.description.toLowerCase().includes(searchFilter.toLowerCase()) &&
        !rule.rule_code.toLowerCase().includes(searchFilter.toLowerCase())) {
      return false;
    }
    return true;
  });

  const formatInputValues = (inputValues: Record<string, any>) => {
    return Object.entries(inputValues)
      .map(([key, value]) => `${key}: ${typeof value === 'number' ? value.toLocaleString() : value}`)
      .join(', ');
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Rules Applied
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Human-readable audit of every rule applied with pass/fail status. 
        Rules are evaluated against tax return data to ensure compliance and accuracy.
      </Typography>

      {/* Summary Cards */}
      {summary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Rules
                </Typography>
                <Typography variant="h4">
                  {summary.total_rules}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Passed
                </Typography>
                <Typography variant="h4" color="success.main">
                  {summary.passed}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Failed
                </Typography>
                <Typography variant="h4" color="error.main">
                  {summary.failed}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Errors
                </Typography>
                <Typography variant="h4" color="error.main">
                  {summary.errors}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <FilterIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Filters
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Search"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search rules..."
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  label="Category"
                >
                  <MenuItem value="">All</MenuItem>
                  {categories.map(category => (
                    <MenuItem key={category} value={category}>
                      {category.replace('_', ' ').toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  label="Severity"
                >
                  <MenuItem value="">All</MenuItem>
                  {severities.map(severity => (
                    <MenuItem key={severity} value={severity}>
                      {severity.toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={passedFilter}
                  onChange={(e) => setPassedFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="true">Passed</MenuItem>
                  <MenuItem value="false">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  onClick={fetchRulesData}
                  startIcon={<RefreshIcon />}
                  disabled={loading}
                >
                  Refresh
                </Button>
                <Button
                  variant="outlined"
                  onClick={clearRulesLog}
                  startIcon={<ClearIcon />}
                  color="warning"
                >
                  Clear Log
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Loading */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Rules Log Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Rules Evaluation Log ({filteredRules.length} results)
          </Typography>
          
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Rule Code</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Input Values</TableCell>
                  <TableCell>Output</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Timestamp</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredRules.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography color="text.secondary">
                        No rules have been evaluated yet. 
                        Rules are automatically evaluated when processing tax returns.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRules.map((rule, index) => (
                    <TableRow key={`${rule.rule_code}-${index}`}>
                      <TableCell>
                        <Tooltip title={rule.passed ? 'Passed' : 'Failed'}>
                          {getPassedIcon(rule.passed)}
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {rule.rule_code}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {rule.description}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getSeverityIcon(rule.severity)}
                          label={rule.severity.toUpperCase()}
                          color={getSeverityColor(rule.severity)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {formatInputValues(rule.input_values)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {String(rule.output_value)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color={rule.passed ? 'success.main' : 'error.main'}>
                          {rule.message}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatTimestamp(rule.timestamp)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Rule Definitions Accordion */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">
                Rule Definitions ({ruleDefinitions.length} rules)
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Code</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell>Expression</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Enabled</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {ruleDefinitions.map((rule) => (
                      <TableRow key={rule.code}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {rule.code}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {rule.description}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={rule.category} size="small" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {rule.expression}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={rule.severity}
                            color={getSeverityColor(rule.severity)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={rule.enabled ? 'Enabled' : 'Disabled'}
                            color={rule.enabled ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Rules;