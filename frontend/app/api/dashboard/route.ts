import { NextResponse } from 'next/server';
import { execSync } from 'child_process';
import path from 'path';

const BACKEND_DIR = path.resolve(process.cwd(), '../backend');
const DB_SCRIPT = path.join(BACKEND_DIR, 'src/db_dashboard.py');

// Helper to execute the python script command and return JSON
function runDbCommand(args: string[]): any {
  try {
    // Quote arguments to handle spaces securely
    const escapedArgs = args.map((arg) => `"${arg.replace(/"/g, '\\"')}"`).join(' ');
    const command = `python "${DB_SCRIPT}" ${escapedArgs}`;
    const output = execSync(command, { cwd: BACKEND_DIR, encoding: 'utf-8' });
    return JSON.parse(output.trim());
  } catch (error: any) {
    console.error('Error executing python db command:', error.message);
    if (error.stdout) {
      console.error('Python stdout:', error.stdout);
    }
    return { error: error.message };
  }
}

export async function GET() {
  const result = runDbCommand(['get']);
  if (result.error) {
    return NextResponse.json(result, { status: 500 });
  }
  return NextResponse.json(result);
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { action } = body;

    if (action === 'update_profile') {
      const { name, email, phone, is_logged_in } = body;
      const result = runDbCommand([
        'update_profile',
        name || '',
        email || '',
        phone || '',
        String(is_logged_in ?? true),
      ]);
      return NextResponse.json(result);
    } else if (action === 'add_transaction') {
      const { type, amount } = body;
      const result = runDbCommand(['add_transaction', type || 'add', String(amount || 0)]);
      return NextResponse.json(result);
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
