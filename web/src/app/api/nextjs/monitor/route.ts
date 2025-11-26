import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const service = searchParams.get('service');

  if (!service) {
    return NextResponse.json({ error: 'service 参数缺失' }, { status: 400 });
  }

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const encoder = new TextEncoder();


      const sendEvent = (event: string, data: unknown) => {
        controller.enqueue(
          encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
        );
      };

      // Heartbeat to keep the connection alive through proxies
      const heartbeat = setInterval(() => {
        controller.enqueue(encoder.encode(`: ping\n\n`));
      }, 15000);

      // Helper to stream a child process by lines
      const streamProcess = (child: ReturnType<typeof spawn>, tag: string) => {
        let stdoutBuffer = '';
        let stderrBuffer = '';

        child.stdout?.on('data', (chunk: Buffer) => {
          stdoutBuffer += chunk.toString();
          const lines = stdoutBuffer.split(/\r?\n/);
          stdoutBuffer = lines.pop() ?? '';
          for (const line of lines) {
            if (line.length > 0) sendEvent(tag, { line });
          }
        });

        child.stderr?.on('data', (chunk: Buffer) => {
          stderrBuffer += chunk.toString();
          const lines = stderrBuffer.split(/\r?\n/);
          stderrBuffer = lines.pop() ?? '';
          for (const line of lines) {
            if (line.length > 0) sendEvent(`${tag}:stderr`, { line });
          }
        });

        child.on('error', (err) => {
          sendEvent('error', { message: err.message });
        });

        child.on('close', (code, signal) => {
          sendEvent('process:close', { tag, code, signal });
        });
      };

      // 1) Send initial status snapshot
      const statusProc = spawn('systemctl', ['status', service, '--no-pager']);
      streamProcess(statusProc, 'status');

      // 2) Follow live logs for the service
      const followProc = spawn('journalctl', [
        '-u',
        service,
        '-f',
        '-n',
        '0',
        '--no-pager',
      ]);
      streamProcess(followProc, 'log');

      // If the client disconnects, clean up
      const onAbort = () => {
        try { statusProc.kill('SIGTERM'); } catch {}
        try { followProc.kill('SIGTERM'); } catch {}
        clearInterval(heartbeat);
        controller.close();
      };


      req.signal?.addEventListener('abort', onAbort);

      // Also auto-close when both processes exit (best-effort)
      let closedCount = 0;
      const tryClose = () => {
        closedCount += 1;
        if (closedCount >= 2) {
          clearInterval(heartbeat);
          controller.close();
        }
      };
      statusProc.on('close', tryClose);
      followProc.on('close', tryClose);

      // Send an initial hello event
      sendEvent('open', { service });
    },
    cancel() {
      // Consumer cancelled; best-effort cleanup happens via abort handler above
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
      'Access-Control-Allow-Origin': '*',
    },
  });
}
