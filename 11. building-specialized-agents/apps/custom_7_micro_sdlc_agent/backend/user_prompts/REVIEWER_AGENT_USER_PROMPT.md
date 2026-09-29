# Review

Conduct a comprehensive review of the implemented work by comparing it against the original plan and assessing code quality.

## Variables

PATH_TO_PLAN: {PATH_TO_PLAN}
REVIEW_OUTPUT_DIRECTORY: {REVIEW_OUTPUT_DIRECTORY}

## Workflow

1. Read the plan at `PATH_TO_PLAN` to understand the intended implementation
2. Run `git diff` to examine all changes made during the build phase
3. Compare the actual implementation against the plan requirements
4. Assess code quality, testing, security, and performance aspects
5. Create a comprehensive review document

## Review Criteria

- **Plan Compliance**: Does the implementation match what was planned?
- **Code Quality**: Is the code clean, well-structured, and maintainable?
- **Functionality**: Does it work as intended?
- **Edge Cases**: Are edge cases and error scenarios handled?
- **Testing**: Is there adequate test coverage?
- **Security**: Are there any security vulnerabilities?
- **Performance**: Are there any performance concerns?
- **Documentation**: Is the code properly documented?

## Report

Save your comprehensive review to `REVIEW_OUTPUT_DIRECTORY/<ticket-name>-review.md` with:
- Executive summary with overall assessment
- Detailed findings for each review criterion
- Specific code examples of issues found
- Recommendations for improvement
- Positive aspects that were well implemented

Return the path to the review file created.