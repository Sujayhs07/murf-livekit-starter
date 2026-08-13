import { NextResponse } from 'next/server';
import { execSync } from 'child_process';
import path from 'path';

const BACKEND_DIR = path.resolve(process.cwd(), '../backend');
const DB_SCRIPT = path.join(BACKEND_DIR, 'src/db_dashboard.py');

function runDbCommand(args: string[]): any {
  try {
    const escapedArgs = args.map((arg) => `"${arg.replace(/"/g, '\\"')}"`).join(' ');
    const command = `python "${DB_SCRIPT}" ${escapedArgs}`;
    const output = execSync(command, { cwd: BACKEND_DIR, encoding: 'utf-8' });
    return JSON.parse(output.trim());
  } catch (error: any) {
    console.error('Error executing python db command:', error.message);
    return { error: error.message };
  }
}

export async function GET() {
  const result = runDbCommand(['get_analytics']);
  if (result.error) {
    return NextResponse.json(result, { status: 500 });
  }
  return NextResponse.json(result);
}
