import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Tree item for the DevBase structure view
 */
export class StructureItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly resourcePath: string,
        public readonly isArea: boolean = false
    ) {
        super(label, collapsibleState);

        this.resourceUri = vscode.Uri.file(resourcePath);

        // Set icon based on type
        if (isArea) {
            this.iconPath = new vscode.ThemeIcon('folder-library');
        } else {
            this.iconPath = new vscode.ThemeIcon('folder');
        }

        // Add context value for menus
        this.contextValue = isArea ? 'area' : 'folder';

        // Add tooltip
        this.tooltip = resourcePath;

        // Allow opening in explorer
        this.command = {
            command: 'revealInExplorer',
            title: 'Open in Explorer',
            arguments: [vscode.Uri.file(resourcePath)]
        };
    }
}

/**
 * Tree data provider for Johnny.Decimal structure
 */
export class StructureProvider implements vscode.TreeDataProvider<StructureItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<StructureItem | undefined | null | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private workspaceRoot: string;

    // Johnny.Decimal areas
    private readonly areas = [
        { pattern: '00-09_', name: '00-09 SYSTEM', icon: '⚙️' },
        { pattern: '10-19_', name: '10-19 KNOWLEDGE', icon: '📚' },
        { pattern: '20-29_', name: '20-29 CODE', icon: '💻' },
        { pattern: '30-39_', name: '30-39 OPERATIONS', icon: '🔧' },
        { pattern: '40-49_', name: '40-49 MEDIA', icon: '🎨' },
        { pattern: '90-99_', name: '90-99 ARCHIVE', icon: '❄️' }
    ];

    constructor(workspaceRoot: string) {
        this.workspaceRoot = workspaceRoot;
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: StructureItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: StructureItem): Thenable<StructureItem[]> {
        if (!this.workspaceRoot) {
            return Promise.resolve([]);
        }

        if (element) {
            // Get children of the element
            return this.getChildFolders(element.resourcePath);
        } else {
            // Get root areas
            return this.getRootAreas();
        }
    }

    private async getRootAreas(): Promise<StructureItem[]> {
        const items: StructureItem[] = [];

        try {
            const entries = await fs.promises.readdir(this.workspaceRoot, { withFileTypes: true });

            for (const area of this.areas) {
                const entry = entries.find(e => e.isDirectory() && e.name.startsWith(area.pattern));

                if (entry) {
                    const fullPath = path.join(this.workspaceRoot, entry.name);
                    const label = `${area.icon} ${entry.name}`;

                    items.push(new StructureItem(
                        label,
                        vscode.TreeItemCollapsibleState.Collapsed,
                        fullPath,
                        true
                    ));
                }
            }
        } catch (error) {
            console.error('Error reading workspace:', error);
        }

        return items;
    }

    private async getChildFolders(folderPath: string): Promise<StructureItem[]> {
        const items: StructureItem[] = [];

        try {
            const entries = await fs.promises.readdir(folderPath, { withFileTypes: true });

            for (const entry of entries) {
                if (entry.isDirectory() && !entry.name.startsWith('.')) {
                    const fullPath = path.join(folderPath, entry.name);

                    items.push(new StructureItem(
                        entry.name,
                        vscode.TreeItemCollapsibleState.Collapsed,
                        fullPath,
                        false
                    ));
                }
            }
        } catch (error) {
            console.error('Error reading folder:', error);
        }

        return items.sort((a, b) => a.label.localeCompare(b.label));
    }
}
