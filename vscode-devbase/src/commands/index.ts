import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

export class DevBaseCommands {
    private context: vscode.ExtensionContext;
    private workspaceRoot: string;
    private outputChannel: vscode.OutputChannel;

    constructor(context: vscode.ExtensionContext, workspaceRoot: string) {
        this.context = context;
        this.workspaceRoot = workspaceRoot;
        this.outputChannel = vscode.window.createOutputChannel('DevBase');
    }

    private getConfig() {
        const config = vscode.workspace.getConfiguration('devbase');
        return {
            pythonPath: config.get<string>('pythonPath') || 'python',
            cliPath: config.get<string>('cliPath') || this.findCliPath()
        };
    }

    private findCliPath(): string {
        // Try to find devbase.py in common locations
        const possiblePaths = [
            path.join(this.workspaceRoot, '30-39_OPERATIONS', '35_devbase_cli', 'devbase.py'),
            path.join(this.workspaceRoot, 'devbase.py'),
        ];

        for (const p of possiblePaths) {
            try {
                require('fs').accessSync(p);
                return p;
            } catch { }
        }

        return 'devbase.py';
    }

    private async runCommand(args: string[]): Promise<string> {
        const config = this.getConfig();
        const cmd = config.pythonPath;
        const fullArgs = [config.cliPath, ...args, '--root', this.workspaceRoot];

        return new Promise((resolve, reject) => {
            const process = cp.spawn(cmd, fullArgs, {
                cwd: this.workspaceRoot,
                shell: true
            });

            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
                this.outputChannel.append(data.toString());
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
                this.outputChannel.append(data.toString());
            });

            process.on('close', (code) => {
                if (code === 0) {
                    resolve(stdout);
                } else {
                    reject(new Error(stderr || `Process exited with code ${code}`));
                }
            });
        });
    }

    async doctor(): Promise<void> {
        this.outputChannel.show();
        this.outputChannel.appendLine('Running DevBase Doctor...\n');

        try {
            const result = await this.runCommand(['doctor']);

            if (result.includes('HEALTHY')) {
                vscode.window.showInformationMessage('✅ DevBase is healthy!');
            } else {
                vscode.window.showWarningMessage('⚠️ DevBase found issues. Check output for details.');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`DevBase Doctor failed: ${error}`);
        }
    }

    async newProject(): Promise<void> {
        const projectName = await vscode.window.showInputBox({
            prompt: 'Enter project name',
            placeHolder: 'my-new-project',
            validateInput: (value) => {
                if (!value) {
                    return 'Project name is required';
                }
                if (!/^[a-z0-9-]+$/.test(value)) {
                    return 'Use lowercase letters, numbers, and hyphens only';
                }
                return null;
            }
        });

        if (!projectName) {
            return;
        }

        this.outputChannel.show();
        this.outputChannel.appendLine(`Creating project: ${projectName}\n`);

        try {
            await this.runCommand(['new', projectName]);
            vscode.window.showInformationMessage(`✅ Project '${projectName}' created!`);
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to create project: ${error}`);
        }
    }

    async track(): Promise<void> {
        const message = await vscode.window.showInputBox({
            prompt: 'What did you work on?',
            placeHolder: 'Implemented feature X'
        });

        if (!message) {
            return;
        }

        const type = await vscode.window.showQuickPick(
            ['work', 'meeting', 'learning', 'review', 'bugfix', 'feature'],
            { placeHolder: 'Select activity type' }
        );

        try {
            await this.runCommand(['track', message, '--type', type || 'work']);
            vscode.window.showInformationMessage(`✅ Tracked: ${message}`);
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to track: ${error}`);
        }
    }

    async dashboard(): Promise<void> {
        vscode.window.showInformationMessage('Opening DevBase Dashboard...');

        // Open in terminal
        const terminal = vscode.window.createTerminal('DevBase Dashboard');
        const config = this.getConfig();
        terminal.sendText(`${config.pythonPath} ${config.cliPath} dashboard --root "${this.workspaceRoot}"`);
        terminal.show();
    }

    async hydrate(): Promise<void> {
        const confirm = await vscode.window.showQuickPick(['Yes', 'No'], {
            placeHolder: 'Hydrate will sync templates. Continue?'
        });

        if (confirm !== 'Yes') {
            return;
        }

        this.outputChannel.show();
        this.outputChannel.appendLine('Running DevBase Hydrate...\n');

        try {
            await this.runCommand(['hydrate']);
            vscode.window.showInformationMessage('✅ Templates synced!');
        } catch (error) {
            vscode.window.showErrorMessage(`Hydrate failed: ${error}`);
        }
    }
}
