import * as vscode from 'vscode';
import * as path from 'path';
import { DevBaseCommands } from './commands/index';
import { StructureProvider } from './providers/structureProvider';
import { RecentActivityProvider } from './providers/recentActivityProvider';

let structureProvider: StructureProvider;
let recentProvider: RecentActivityProvider;

export function activate(context: vscode.ExtensionContext) {
    console.log('DevBase extension is now active!');

    // Get workspace root
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    if (!workspaceRoot) {
        vscode.window.showWarningMessage('DevBase: No workspace folder open');
        return;
    }

    // Initialize commands
    const commands = new DevBaseCommands(context, workspaceRoot);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('devbase.doctor', () => commands.doctor()),
        vscode.commands.registerCommand('devbase.newProject', () => commands.newProject()),
        vscode.commands.registerCommand('devbase.track', () => commands.track()),
        vscode.commands.registerCommand('devbase.dashboard', () => commands.dashboard()),
        vscode.commands.registerCommand('devbase.hydrate', () => commands.hydrate())
    );

    // Initialize tree views
    structureProvider = new StructureProvider(workspaceRoot);
    recentProvider = new RecentActivityProvider(workspaceRoot);

    vscode.window.registerTreeDataProvider('devbaseStructure', structureProvider);
    vscode.window.registerTreeDataProvider('devbaseRecent', recentProvider);

    // Refresh tree views
    context.subscriptions.push(
        vscode.commands.registerCommand('devbase.refreshStructure', () => structureProvider.refresh()),
        vscode.commands.registerCommand('devbase.refreshRecent', () => recentProvider.refresh())
    );

    // Status bar item
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBar.text = '$(rocket) DevBase';
    statusBar.command = 'devbase.doctor';
    statusBar.tooltip = 'DevBase: Click to run doctor';
    statusBar.show();
    context.subscriptions.push(statusBar);
}

export function deactivate() {
    console.log('DevBase extension is now deactivated');
}
