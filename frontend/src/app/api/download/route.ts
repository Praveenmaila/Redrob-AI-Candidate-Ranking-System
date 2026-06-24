import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_TARGET || "http://localhost:8000";
  try {
    const res = await fetch(`${backendUrl}/download`);
    if (!res.ok) {
      return NextResponse.json(
        { error: "File not found on backend" },
        { status: res.status }
      );
    }
    const csvText = await res.text();
    return new NextResponse(csvText, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition":
          'attachment; filename="submission_top100.csv"',
      },
    });
  } catch (e) {
    return NextResponse.json(
      { error: "Backend not reachable" },
      { status: 502 }
    );
  }
}
