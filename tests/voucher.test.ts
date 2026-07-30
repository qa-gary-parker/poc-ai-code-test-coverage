import { describe, expect, it } from "vitest";
import { applyVouchers, type Basket, type Voucher } from "../src/voucher";

const NOW = new Date("2026-07-15T12:00:00Z");

function basket(...items: [unitPricePence: number, quantity: number][]): Basket {
  return { items: items.map(([unitPricePence, quantity]) => ({ unitPricePence, quantity })) };
}

function pct(code: string, value: number, extra: Partial<Voucher> = {}): Voucher {
  return { code, kind: "percentage", value, ...extra };
}

function fixed(code: string, value: number, extra: Partial<Voucher> = {}): Voucher {
  return { code, kind: "fixed", value, ...extra };
}

describe("subtotal", () => {
  it("sums unitPricePence * quantity across items", () => {
    const result = applyVouchers(basket([250, 2], [100, 3]), [], NOW);
    expect(result).toEqual({ subtotalPence: 800, discountPence: 0, totalPence: 800, applied: [] });
  });

  it("ignores items with quantity zero", () => {
    const result = applyVouchers(basket([500, 1], [999, 0]), [], NOW);
    expect(result.subtotalPence).toBe(500);
  });

  it("returns zero for an empty basket", () => {
    const result = applyVouchers(basket(), [], NOW);
    expect(result).toEqual({ subtotalPence: 0, discountPence: 0, totalPence: 0, applied: [] });
  });

  it("throws RangeError for a negative unit price", () => {
    expect(() => applyVouchers(basket([-1, 1]), [], NOW)).toThrow(RangeError);
  });

  it("throws RangeError for a negative quantity", () => {
    expect(() => applyVouchers(basket([100, -2]), [], NOW)).toThrow(RangeError);
  });

  it("accepts free (zero-price) items such as promotional gifts", () => {
    const result = applyVouchers(basket([0, 3], [500, 1]), [], NOW);
    expect(result.subtotalPence).toBe(500);
  });

  it("names the offending value when rejecting a negative unit price", () => {
    expect(() => applyVouchers(basket([-50, 1]), [], NOW)).toThrow(
      "Invalid unit price: -50",
    );
  });

  it("names the offending value when rejecting a negative quantity", () => {
    expect(() => applyVouchers(basket([100, -2]), [], NOW)).toThrow(
      "Invalid quantity: -2",
    );
  });
});

describe("percentage vouchers", () => {
  it("discounts a percentage of the subtotal", () => {
    const result = applyVouchers(basket([1000, 1]), [pct("TEN", 10)], NOW);
    expect(result).toEqual({ subtotalPence: 1000, discountPence: 100, totalPence: 900, applied: ["TEN"] });
  });

  it("rounds half up to the nearest penny", () => {
    // 10% of 1005 = 100.5 -> 101
    expect(applyVouchers(basket([1005, 1]), [pct("TEN", 10)], NOW).discountPence).toBe(101);
    // 2.5% of 1020 = 25.5 -> 26
    expect(applyVouchers(basket([1020, 1]), [pct("SMALL", 2.5)], NOW).discountPence).toBe(26);
  });

  it("rounds down below the half-penny", () => {
    // 10% of 1004 = 100.4 -> 100
    expect(applyVouchers(basket([1004, 1]), [pct("TEN", 10)], NOW).discountPence).toBe(100);
  });

  it("computes each percentage from the original subtotal, not the running total", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [pct("A", 10, { stackable: true }), pct("B", 10, { stackable: true })],
      NOW,
    );
    // 100 + 100, not 100 + 90
    expect(result.discountPence).toBe(200);
    expect(result.totalPence).toBe(800);
  });

  it("computes a percentage from the original subtotal even after a fixed discount", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [fixed("F", 500, { stackable: true }), pct("P", 10, { stackable: true })],
      NOW,
    );
    expect(result.discountPence).toBe(600);
    expect(result.totalPence).toBe(400);
  });
});

describe("fixed vouchers", () => {
  it("discounts the face value", () => {
    const result = applyVouchers(basket([1000, 1]), [fixed("OFF250", 250)], NOW);
    expect(result).toEqual({ subtotalPence: 1000, discountPence: 250, totalPence: 750, applied: ["OFF250"] });
  });
});

describe("minimum spend", () => {
  it("applies when the subtotal equals minSpendPence", () => {
    const result = applyVouchers(basket([500, 2]), [fixed("MIN", 100, { minSpendPence: 1000 })], NOW);
    expect(result.applied).toEqual(["MIN"]);
    expect(result.totalPence).toBe(900);
  });

  it("does not apply when the subtotal is below minSpendPence", () => {
    const result = applyVouchers(basket([999, 1]), [fixed("MIN", 100, { minSpendPence: 1000 })], NOW);
    expect(result).toEqual({ subtotalPence: 999, discountPence: 0, totalPence: 999, applied: [] });
  });
});

describe("expiry", () => {
  it("does not apply an expired voucher", () => {
    const result = applyVouchers(basket([1000, 1]), [pct("OLD", 10, { expiresAt: "2026-07-14" })], NOW);
    expect(result.applied).toEqual([]);
    expect(result.totalPence).toBe(1000);
  });

  it("remains valid for the whole of the expiry day, UTC", () => {
    const endOfDay = new Date("2026-07-15T23:59:59.999Z");
    const result = applyVouchers(basket([1000, 1]), [pct("TODAY", 10, { expiresAt: "2026-07-15" })], endOfDay);
    expect(result.applied).toEqual(["TODAY"]);
  });

  it("expires at UTC midnight after the expiry day", () => {
    const justAfter = new Date("2026-07-16T00:00:00.000Z");
    const result = applyVouchers(basket([1000, 1]), [pct("TODAY", 10, { expiresAt: "2026-07-15" })], justAfter);
    expect(result.applied).toEqual([]);
  });

  it("treats a timestamped expiresAt as valid for its whole calendar day", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [pct("TS", 10, { expiresAt: "2026-07-15T00:00:00.000Z" })],
      new Date("2026-07-15T18:00:00Z"),
    );
    expect(result.applied).toEqual(["TS"]);
  });

  it("never expires without an expiresAt", () => {
    const farFuture = new Date("2099-01-01T00:00:00Z");
    const result = applyVouchers(basket([1000, 1]), [pct("EVERGREEN", 10)], farFuture);
    expect(result.applied).toEqual(["EVERGREEN"]);
  });
});

describe("stacking", () => {
  it("applies only the largest of several non-stackable vouchers", () => {
    const result = applyVouchers(basket([1000, 1]), [fixed("SMALL", 100), fixed("BIG", 300)], NOW);
    expect(result.applied).toEqual(["BIG"]);
    expect(result.totalPence).toBe(700);
  });

  it("treats vouchers as non-stackable by default", () => {
    const result = applyVouchers(basket([1000, 1]), [pct("A", 10), pct("B", 20)], NOW);
    expect(result.applied).toEqual(["B"]);
    expect(result.discountPence).toBe(200);
  });

  it("compares percentage and fixed non-stackables by discount given", () => {
    // 30% of 1000 = 300 beats fixed 250
    const result = applyVouchers(basket([1000, 1]), [fixed("F", 250), pct("P", 30)], NOW);
    expect(result.applied).toEqual(["P"]);
    expect(result.totalPence).toBe(700);
  });

  it("applies all eligible stackable vouchers alongside the best non-stackable", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [
        fixed("NS1", 100),
        pct("S1", 10, { stackable: true }),
        fixed("NS2", 200),
        fixed("S2", 50, { stackable: true }),
      ],
      NOW,
    );
    expect(result.applied).toEqual(["S1", "NS2", "S2"]);
    expect(result.discountPence).toBe(350);
    expect(result.totalPence).toBe(650);
  });

  it("applies all stackable vouchers when there is no non-stackable one", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [fixed("A", 100, { stackable: true }), fixed("B", 200, { stackable: true })],
      NOW,
    );
    expect(result.applied).toEqual(["A", "B"]);
    expect(result.totalPence).toBe(700);
  });

  it("applies the largest non-stackable even when it is listed first", () => {
    const result = applyVouchers(basket([1000, 1]), [fixed("BIG", 300), fixed("SMALL", 100)], NOW);
    expect(result.applied).toEqual(["BIG"]);
    expect(result.totalPence).toBe(700);
  });

  it("breaks ties between equal non-stackable vouchers in favour of the first", () => {
    const result = applyVouchers(basket([1000, 1]), [fixed("FIRST", 200), fixed("SECOND", 200)], NOW);
    expect(result.applied).toEqual(["FIRST"]);
    expect(result.discountPence).toBe(200);
  });

  it("does not let a large stackable voucher displace the best non-stackable", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [fixed("STACK", 500, { stackable: true }), fixed("SOLO", 100)],
      NOW,
    );
    expect(result.applied).toEqual(["STACK", "SOLO"]);
    expect(result.discountPence).toBe(600);
    expect(result.totalPence).toBe(400);
  });

  it("ignores ineligible vouchers when choosing the best non-stackable", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [fixed("HUGE-EXPIRED", 900, { expiresAt: "2026-01-01" }), fixed("OK", 100)],
      NOW,
    );
    expect(result.applied).toEqual(["OK"]);
    expect(result.totalPence).toBe(900);
  });
});

describe("floor and capping", () => {
  it("caps a fixed discount at the subtotal", () => {
    const result = applyVouchers(basket([300, 1]), [fixed("BIG", 1000)], NOW);
    expect(result).toEqual({ subtotalPence: 300, discountPence: 300, totalPence: 0, applied: ["BIG"] });
  });

  it("caps a voucher at the remaining total when earlier vouchers already discounted", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [fixed("A", 800, { stackable: true }), fixed("B", 500, { stackable: true })],
      NOW,
    );
    expect(result.applied).toEqual(["A", "B"]);
    expect(result.discountPence).toBe(1000);
    expect(result.totalPence).toBe(0);
  });

  it("never produces a negative total", () => {
    const result = applyVouchers(
      basket([100, 1]),
      [pct("P", 100, { stackable: true }), fixed("F", 500, { stackable: true })],
      NOW,
    );
    expect(result.totalPence).toBe(0);
    expect(result.discountPence).toBe(100);
  });
});

describe("duplicate codes", () => {
  it("counts only the first occurrence of a code", () => {
    const result = applyVouchers(basket([1000, 1]), [pct("DUP", 10), pct("DUP", 50)], NOW);
    expect(result.applied).toEqual(["DUP"]);
    expect(result.discountPence).toBe(100);
  });

  it("does not double-apply a duplicated stackable code", () => {
    const result = applyVouchers(
      basket([1000, 1]),
      [fixed("DUP", 100, { stackable: true }), fixed("DUP", 100, { stackable: true })],
      NOW,
    );
    expect(result.applied).toEqual(["DUP"]);
    expect(result.discountPence).toBe(100);
  });
});

describe("result shape", () => {
  it("lists applied codes in application order and keeps totals consistent", () => {
    const result = applyVouchers(
      basket([2000, 1]),
      [
        pct("S1", 5, { stackable: true }),
        fixed("NS", 300),
        fixed("S2", 100, { stackable: true }),
      ],
      NOW,
    );
    expect(result.applied).toEqual(["S1", "NS", "S2"]);
    expect(result.subtotalPence).toBe(2000);
    expect(result.discountPence).toBe(500);
    expect(result.totalPence).toBe(result.subtotalPence - result.discountPence);
  });

  it("applies an eligible voucher to an empty basket without going negative", () => {
    const result = applyVouchers(basket(), [fixed("FREE", 100)], NOW);
    expect(result).toEqual({ subtotalPence: 0, discountPence: 0, totalPence: 0, applied: ["FREE"] });
  });
});
