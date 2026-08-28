import { GlobalErrorCode } from './global_error_code';

export class BaseSystemException extends Error {
    public readonly errorCode: GlobalErrorCode;
    public readonly details?: Record<string, unknown>;

    constructor(
        errorCode: GlobalErrorCode,
        message?: string,
        details?: Record<string, unknown>,
        options?: ErrorOptions,
    ) {
        super(message || errorCode, options);
        this.name = 'BaseSystemException';
        this.errorCode = errorCode;
        this.details = details;
        Object.setPrototypeOf(this, BaseSystemException.prototype);
    }

    public static fromErrorCode(
        errorCode: GlobalErrorCode,
        customMessage?: string,
        details?: Record<string, unknown>,
        cause?: Error,
    ): BaseSystemException {
        return new BaseSystemException(errorCode, customMessage, details, cause ? { cause } : undefined);
    }
}
