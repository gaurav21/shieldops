'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown } from 'lucide-react';
import { Repository } from '@/lib/api';

interface ConfigPanelProps {
  repository: Repository;
  onConfigUpdate: (config: Partial<Record<string, any>>) => Promise<void>;
}

const scanTypeOptions = [
  { id: 'pip-audit', label: 'pip-audit (Python)' },
  { id: 'npm-audit', label: 'npm audit (Node.js)' },
  { id: 'trivy', label: 'Trivy (Multi-language)' },
  { id: 'semgrep', label: 'Semgrep (SAST)' }
];

const severityThresholds = [
  { value: 'low', label: 'Low', description: 'Include all vulnerabilities' },
  { value: 'medium', label: 'Medium', description: 'Medium severity and above' },
  { value: 'high', label: 'High', description: 'High severity and above' },
  { value: 'critical', label: 'Critical', description: 'Critical vulnerabilities only' }
];

export function ConfigPanel({ repository, onConfigUpdate }: ConfigPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState(repository.scan_config);
  
  const handleSave = async () => {
    setLoading(true);
    try {
      await onConfigUpdate(config);
    } finally {
      setLoading(false);
    }
  };
  
  const toggleScanType = (scanType: string) => {
    const newScanTypes = config.scan_types.includes(scanType)
      ? config.scan_types.filter(t => t !== scanType)
      : [...config.scan_types, scanType];
    setConfig({ ...config, scan_types: newScanTypes });
  };
  
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CardHeader 
          className="cursor-pointer hover:bg-muted/50" 
          onClick={() => setIsOpen(!isOpen)}
        >
          <CardTitle className="flex items-center justify-between">
            Repository Configuration
            <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </CardTitle>
        </CardHeader>
        
        <CollapsibleContent>
          <CardContent className="space-y-6">
            {/* Scan Types */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Scan Types</Label>
              <div className="grid grid-cols-2 gap-3">
                {scanTypeOptions.map((option) => (
                  <div key={option.id} className="flex items-center space-x-2">
                    <Switch
                      id={option.id}
                      checked={config.scan_types.includes(option.id)}
                      onCheckedChange={() => toggleScanType(option.id)}
                    />
                    <Label htmlFor={option.id} className="text-sm">
                      {option.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Schedule */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Scan Schedule</Label>
              <Select value={config.schedule} onValueChange={(value: any) => setConfig({ ...config, schedule: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="on-push">On Git Push</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Auto-fix */}
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm font-medium">Auto-fix Enabled</Label>
                <p className="text-xs text-muted-foreground mt-1">
                  Automatically create PRs for vulnerability fixes
                </p>
              </div>
              <Switch
                checked={config.auto_fix}
                onCheckedChange={(checked) => setConfig({ ...config, auto_fix: checked })}
              />
            </div>
            
            {/* Severity Threshold */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Severity Threshold</Label>
              <Select 
                value={config.severity_threshold} 
                onValueChange={(value: any) => setConfig({ ...config, severity_threshold: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {severityThresholds.map((threshold) => (
                    <SelectItem key={threshold.value} value={threshold.value}>
                      <div>
                        <div className="font-medium">{threshold.label}</div>
                        <div className="text-xs text-muted-foreground">{threshold.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={loading}>
                {loading ? 'Saving...' : 'Save Configuration'}
              </Button>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}