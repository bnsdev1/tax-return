import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Switch } from '../components/ui/switch';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface LLMSettings {
  id: number;
  llm_enabled: boolean;
  cloud_allowed: boolean;
  primary: string;
  long_context_provider: string;
  local_provider: string;
  redact_pii: boolean;
  long_context_threshold_chars: number;
  confidence_threshold: number;
  max_retries: number;
  timeout_ms: number;
  created_at: string;
  updated_at?: string;
}

interface Provider {
  name: string;
  display_name: string;
  type: 'cloud' | 'local';
  description: string;
}

interface PingResult {
  ok: boolean;
  provider: string;
  model?: string;
  response_time_ms?: number;
  error?: string;
}

const SettingsLLM: React.FC = () => {
  const [settings, setSettings] = useState<LLMSettings | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pingResults, setPingResults] = useState<Record<string, PingResult>>({});
  const [pingingProvider, setPingingProvider] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
    loadProviders();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/settings/llm');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      } else {
        setError('Failed to load LLM settings');
      }
    } catch (err) {
      setError('Error loading settings');
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/settings/llm/providers');
      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers);
      }
    } catch (err) {
      console.error('Error loading providers:', err);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/settings/llm', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        const updatedSettings = await response.json();
        setSettings(updatedSettings);
        setSuccess('Settings saved successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to save settings');
      }
    } catch (err) {
      setError('Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  const pingProvider = async (providerName: string) => {
    setPingingProvider(providerName);
    
    try {
      const response = await fetch('/api/settings/llm/ping', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider: providerName }),
      });

      if (response.ok) {
        const result = await response.json();
        setPingResults(prev => ({ ...prev, [providerName]: result }));
      } else {
        const errorData = await response.json();
        setPingResults(prev => ({
          ...prev,
          [providerName]: {
            ok: false,
            provider: providerName,
            error: errorData.detail || 'Ping failed'
          }
        }));
      }
    } catch (err) {
      setPingResults(prev => ({
        ...prev,
        [providerName]: {
          ok: false,
          provider: providerName,
          error: 'Network error'
        }
      }));
    } finally {
      setPingingProvider(null);
    }
  };

  const updateSetting = (key: keyof LLMSettings, value: any) => {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  };

  const getPingStatusIcon = (providerName: string) => {
    const result = pingResults[providerName];
    if (!result) return null;
    
    if (result.ok) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else {
      return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!settings) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Failed to load LLM settings</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">AI Settings</h1>
        <Button onClick={saveSettings} disabled={saving}>
          {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Save Settings
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {/* Core Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Core Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="llm-enabled"
              checked={settings.llm_enabled}
              onCheckedChange={(checked: boolean) => updateSetting('llm_enabled', checked)}
            />
            <Label htmlFor="llm-enabled">Enable LLM Processing</Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="cloud-allowed"
              checked={settings.cloud_allowed}
              onCheckedChange={(checked: boolean) => updateSetting('cloud_allowed', checked)}
              disabled={!settings.llm_enabled}
            />
            <Label htmlFor="cloud-allowed">Allow Cloud Providers</Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="redact-pii"
              checked={settings.redact_pii}
              onCheckedChange={(checked: boolean) => updateSetting('redact_pii', checked)}
              disabled={!settings.llm_enabled || !settings.cloud_allowed}
            />
            <Label htmlFor="redact-pii">Redact PII for Cloud</Label>
          </div>
        </CardContent>
      </Card>

      {/* Provider Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Provider Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="primary-provider">Primary Provider</Label>
              <Select
                value={settings.primary}
                onValueChange={(value: string) => updateSetting('primary', value)}
                disabled={!settings.llm_enabled}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {providers.filter(p => p.type === 'cloud').map(provider => (
                    <SelectItem key={provider.name} value={provider.name}>
                      {provider.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="long-context-provider">Long Context Provider</Label>
              <Select
                value={settings.long_context_provider}
                onValueChange={(value: string) => updateSetting('long_context_provider', value)}
                disabled={!settings.llm_enabled}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {providers.filter(p => p.type === 'cloud').map(provider => (
                    <SelectItem key={provider.name} value={provider.name}>
                      {provider.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="local-provider">Local Provider</Label>
              <Select
                value={settings.local_provider}
                onValueChange={(value: string) => updateSetting('local_provider', value)}
                disabled={!settings.llm_enabled}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {providers.filter(p => p.type === 'local').map(provider => (
                    <SelectItem key={provider.name} value={provider.name}>
                      {provider.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Provider Testing */}
      <Card>
        <CardHeader>
          <CardTitle>Provider Testing</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {providers.map(provider => (
              <div key={provider.name} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">{provider.display_name}</h3>
                  <div className="flex items-center space-x-2">
                    {getPingStatusIcon(provider.name)}
                    <Badge variant={provider.type === 'cloud' ? 'default' : 'secondary'}>
                      {provider.type}
                    </Badge>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3">{provider.description}</p>
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => pingProvider(provider.name)}
                  disabled={pingingProvider === provider.name || !settings.llm_enabled}
                  className="w-full"
                >
                  {pingingProvider === provider.name ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    `Ping ${provider.display_name}`
                  )}
                </Button>

                {pingResults[provider.name] && (
                  <div className="mt-2 text-xs">
                    {pingResults[provider.name].ok ? (
                      <div className="text-green-600">
                        ✓ Connected ({pingResults[provider.name].response_time_ms}ms)
                        {pingResults[provider.name].model && (
                          <div>Model: {pingResults[provider.name].model}</div>
                        )}
                      </div>
                    ) : (
                      <div className="text-red-600">
                        ✗ {pingResults[provider.name].error}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Advanced Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="long-context-threshold">Long Context Threshold (chars)</Label>
              <Input
                id="long-context-threshold"
                type="number"
                value={settings.long_context_threshold_chars}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateSetting('long_context_threshold_chars', parseInt(e.target.value))}
                disabled={!settings.llm_enabled}
                min="1000"
                max="50000"
              />
            </div>

            <div>
              <Label htmlFor="confidence-threshold">Confidence Threshold</Label>
              <Input
                id="confidence-threshold"
                type="number"
                step="0.1"
                value={settings.confidence_threshold}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateSetting('confidence_threshold', parseFloat(e.target.value))}
                disabled={!settings.llm_enabled}
                min="0"
                max="1"
              />
            </div>

            <div>
              <Label htmlFor="max-retries">Max Retries</Label>
              <Input
                id="max-retries"
                type="number"
                value={settings.max_retries}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateSetting('max_retries', parseInt(e.target.value))}
                disabled={!settings.llm_enabled}
                min="0"
                max="5"
              />
            </div>

            <div>
              <Label htmlFor="timeout">Timeout (ms)</Label>
              <Input
                id="timeout"
                type="number"
                value={settings.timeout_ms}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateSetting('timeout_ms', parseInt(e.target.value))}
                disabled={!settings.llm_enabled}
                min="1000"
                max="120000"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsLLM;