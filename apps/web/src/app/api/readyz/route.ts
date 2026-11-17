import { upstream } from "../../../lib/upstream";
export function GET() { return upstream("/readyz"); }
