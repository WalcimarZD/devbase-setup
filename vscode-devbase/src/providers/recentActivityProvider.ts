import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

interface TelemetryEvent {
    timestamp: string;
    type: string;
    message: string;
}

/**
 * Tree item for recent activity
 */
export class ActivityItem extends vscode.TreeItem {
    constructor(
        public readonly event: TelemetryEvent
    ) {
        const date = new Date(event.timestamp);
        const timeAgo = formatTimeAgo(date);

        super(`${event.message}`, vscode.TreeItemCollapsibleState.None);

        // Set icon based on type
        const iconMap: { [key: string]: string } = {
            'work': 'wrench',
            'meeting': 'comment-discussion',
            'learning': 'book',
            'review': 'eye',
            'bugfix': 'bug',
            'feature': 'sparkle'
        };

        this.iconPath = new vscode.ThemeIcon(iconMap[event.type] || 'circle-outline');
        this.description = `${event.type} • ${timeAgo}`;
        this.tooltip = `${event.message}\n\nType: ${event.type}\nTime: ${date.toLocaleString()}`;
    }
}

function formatTimeAgo(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

/**
 * Tree data provider for recent activity
 */
export class RecentActivityProvider implements vscode.TreeDataProvider<ActivityItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ActivityItem | undefined | null | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private workspaceRoot: string;

    constructor(workspaceRoot: string) {
        this.workspaceRoot = workspaceRoot;
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ActivityItem): vscode.TreeItem {
        return element;
    }

    async getChildren(): Promise<ActivityItem[]> {
        const eventsFile = path.join(this.workspaceRoot, '.telemetry', 'events.jsonl');

        if (!fs.existsSync(eventsFile)) {
            return [];
        }

        try {
            const content = await fs.promises.readFile(eventsFile, 'utf-8');
            const lines = content.trim().split('\n').filter(Boolean);

            const events: TelemetryEvent[] = [];

            for (const line of lines) {
                try {
                    events.push(JSON.parse(line));
                } catch { }
            }

            // Sort by timestamp descending and take last 10
            return events
                .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                .slice(0, 10)
                .map(e => new ActivityItem(e));

        } catch (error) {
            console.error('Error reading telemetry:', error);
            return [];
        }
    }
}
