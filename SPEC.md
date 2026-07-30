# Voucher Engine — Functional Specification

Implement `applyVouchers(basket, vouchers, now)` in `src/voucher.ts` (TypeScript,
no dependencies). It calculates the final price of a basket after applying
discount vouchers.

## Inputs

```ts
interface Basket {
  items: { unitPricePence: number; quantity: number }[];
}

interface Voucher {
  code: string;
  kind: "percentage" | "fixed";
  value: number;            // percentage points (e.g. 10 = 10%) or pence
  minSpendPence?: number;   // basket subtotal must meet this to qualify
  expiresAt?: string;       // ISO date; voucher is valid ON its expiry date
  stackable?: boolean;      // default false
}
```

`now` is a `Date` used for expiry checks.

## Rules

1. **Subtotal** = sum of `unitPricePence * quantity` across items. Quantities of
   zero contribute nothing. Negative prices or quantities are invalid input —
   throw `RangeError`.
2. **Eligibility**: a voucher is applied only if (a) it has not expired —
   a voucher expiring today is still valid for the whole of that calendar day,
   UTC; and (b) the basket subtotal is **greater than or equal to**
   `minSpendPence` when present.
3. **Stacking**: at most one non-stackable voucher may be applied — the one that
   gives the largest discount. All eligible stackable vouchers apply, in addition
   to the chosen non-stackable one (if any).
4. **Order of application**: percentage vouchers apply to the subtotal
   independently (each computes its discount from the original subtotal, not the
   running total). Fixed vouchers discount their face value.
5. **Rounding**: percentage discounts round **half up** to the nearest penny.
6. **Floor**: the final total never goes below zero, and a single voucher's
   discount is capped at the remaining total when applied.
7. **Duplicate codes**: if the same code appears twice in `vouchers`, only the
   first occurrence counts.

## Output

```ts
interface Result {
  subtotalPence: number;
  discountPence: number;
  totalPence: number;
  applied: string[];  // codes of applied vouchers, in application order
}
```

## Your task

1. Implement the module in `src/voucher.ts`.
2. Write a test suite in `tests/voucher.test.ts` (Vitest) that you consider
   complete — the tests you would ship to production alongside this module.
