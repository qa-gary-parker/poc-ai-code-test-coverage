export interface Basket {
  items: { unitPricePence: number; quantity: number }[];
}

export interface Voucher {
  code: string;
  kind: "percentage" | "fixed";
  value: number;
  minSpendPence?: number;
  expiresAt?: string;
  stackable?: boolean;
}

export interface Result {
  subtotalPence: number;
  discountPence: number;
  totalPence: number;
  applied: string[];
}

export function applyVouchers(
  basket: Basket,
  vouchers: Voucher[],
  now: Date,
): Result {
  let subtotalPence = 0;
  for (const { unitPricePence, quantity } of basket.items) {
    if (unitPricePence < 0) {
      throw new RangeError(`Invalid unit price: ${unitPricePence}`);
    }
    if (quantity < 0) {
      throw new RangeError(`Invalid quantity: ${quantity}`);
    }
    subtotalPence += unitPricePence * quantity;
  }

  const seenCodes = new Set<string>();
  const candidates = vouchers.filter((v) => {
    if (seenCodes.has(v.code)) return false;
    seenCodes.add(v.code);
    return isEligible(v, subtotalPence, now);
  });

  // Nominal discount a voucher would give against the full subtotal.
  const nominalDiscount = (v: Voucher): number =>
    v.kind === "percentage"
      ? Math.round((subtotalPence * v.value) / 100)
      : v.value;

  let bestNonStackable: Voucher | undefined;
  let bestDiscount = -Infinity;
  for (const v of candidates) {
    if (v.stackable) continue;
    const discount = Math.min(nominalDiscount(v), subtotalPence);
    if (discount > bestDiscount) {
      bestNonStackable = v;
      bestDiscount = discount;
    }
  }

  const applied: string[] = [];
  let totalPence = subtotalPence;
  for (const v of candidates) {
    if (!v.stackable && v !== bestNonStackable) continue;
    totalPence -= Math.min(nominalDiscount(v), totalPence);
    applied.push(v.code);
  }

  return {
    subtotalPence,
    discountPence: subtotalPence - totalPence,
    totalPence,
    applied,
  };
}

function isEligible(v: Voucher, subtotalPence: number, now: Date): boolean {
  if (v.minSpendPence !== undefined && subtotalPence < v.minSpendPence) {
    return false;
  }
  if (v.expiresAt !== undefined) {
    const expiry = new Date(v.expiresAt);
    // Valid for the whole of the expiry calendar day, UTC.
    const endOfExpiryDay = Date.UTC(
      expiry.getUTCFullYear(),
      expiry.getUTCMonth(),
      expiry.getUTCDate() + 1,
    );
    if (!(now.getTime() < endOfExpiryDay)) return false;
  }
  return true;
}
