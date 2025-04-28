import * as path from "path";

const findErrors = (expected, actual, previousKeys) => {
  const errors = [];
  for (const key in expected) {
    if (typeof expected[key] === "object" && expected[key] !== null) {
      errors.push(
        ...findErrors(expected[key], actual[key], [...previousKeys, key])
      );
    } else if (!Object.is(actual[key], expected[key])) {
      let error = `For key "${previousKeys.join(".")}.${key}"`;
      error += ` we got "${actual[key]}"`;
      error += ` but expected "${expected[key]}" instead`;
      errors.push(error);
    }
  }
  for (const key in actual) {
    if (!(key in expected)) {
      let error = `Key "${previousKeys.join(".")}.${key}"`;
      error += " exists but should not.";
      errors.push(error);
    }
  }
  return errors;
};

// chai's deep.equal does not return explicit error messages...
// So we use our own implementation.
export const deepEqual = (expected, actual) => {
  const keys = findErrors(expected, actual, []);
  expect(keys, keys[0]).to.be.empty;
};
