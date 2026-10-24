import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../alerts/presentation/alerts_providers.dart';
import '../../../dashboard/presentation/dashboard_providers.dart';
import '../../../reorder/presentation/reorder_providers.dart';
import '../../domain/models/product.dart';
import '../catalog_providers.dart';

class ClosingAuditDialog extends ConsumerStatefulWidget {
  const ClosingAuditDialog({
    required this.products,
    required this.storeId,
    super.key,
  });

  final List<Product> products;
  final int storeId;

  @override
  ConsumerState<ClosingAuditDialog> createState() => _ClosingAuditDialogState();
}

class _ClosingAuditDialogState extends ConsumerState<ClosingAuditDialog> {
  final _formKey = GlobalKey<FormState>();
  final Map<int, TextEditingController> _onHandControllers = {};
  final Map<int, TextEditingController> _spoiledControllers = {};
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    for (final product in widget.products) {
      _onHandControllers[product.id] =
          TextEditingController(text: product.currentStock.toString());
      _spoiledControllers[product.id] = TextEditingController(text: '0');
    }
  }

  @override
  void dispose() {
    for (final controller in _onHandControllers.values) {
      controller.dispose();
    }
    for (final controller in _spoiledControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _submitAudit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final entries = widget.products.map((p) {
        final onHand = int.parse(_onHandControllers[p.id]!.text.trim());
        final spoiled = int.parse(_spoiledControllers[p.id]!.text.trim());
        return AuditEntry(
          productId: p.id,
          onHandQty: onHand,
          spoiledQty: spoiled,
        );
      }).toList();

      final repository = ref.read(catalogRepositoryProvider);
      await repository.submitAudit(widget.storeId, entries);

      if (!mounted) return;

      ref.invalidate(productsProvider);
      ref.invalidate(dashboardMetricsProvider);
      ref.invalidate(recommendationsProvider);
      ref.invalidate(alertsProvider);

      Navigator.of(context).pop();

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Audit submitted'),
          backgroundColor: AppColors.safe,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to submit audit: $e'),
          backgroundColor: AppColors.critical,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      
      appBar: AppBar(
        backgroundColor: context.isDarkMode ? AppColors.darkSurface : AppColors.forestGreen,
        foregroundColor: Colors.white,
        title: Text(
          'Closing Inventory Audit',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        leading: IconButton(
          icon: Icon(Icons.close_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: AppColors.surfaceVariant,
              child: Row(
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    color: context.primaryBrand,
                    size: 20,
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Store #${widget.storeId}: Confirm physical on-hand units and report any spoiled inventory discarded today.',
                      style: TextStyle(
                        fontSize: 12,
                        color: context.primaryBrand,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Form(
                key: _formKey,
                child: ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: widget.products.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final product = widget.products[index];
                    return Card(
                      elevation: 1,
                      color: context.surfaceColor,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: context.cardBorderColor),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(14.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              product.name,
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.bold,
                                color: context.textColor,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'SKU: ${product.sku} · Recorded Stock: ${product.currentStock}',
                              style: TextStyle(
                                fontSize: 12,
                                color: context.textSecondaryColor,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                Expanded(
                                  child: TextFormField(
                                    controller: _onHandControllers[product.id],
                                    keyboardType: TextInputType.number,
                                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                                    decoration: const InputDecoration(
                                      labelText: 'On-hand Qty',
                                      contentPadding: EdgeInsets.symmetric(
                                        horizontal: 12,
                                        vertical: 10,
                                      ),
                                    ),
                                    validator: (value) {
                                      if (value == null || value.trim().isEmpty) {
                                        return 'Required';
                                      }
                                      final parsed = int.tryParse(value.trim());
                                      if (parsed == null || parsed < 0) {
                                        return 'Invalid';
                                      }
                                      return null;
                                    },
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: TextFormField(
                                    controller: _spoiledControllers[product.id],
                                    keyboardType: TextInputType.number,
                                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                                    decoration: const InputDecoration(
                                      labelText: 'Spoiled Qty',
                                      contentPadding: EdgeInsets.symmetric(
                                        horizontal: 12,
                                        vertical: 10,
                                      ),
                                    ),
                                    validator: (value) {
                                      if (value == null || value.trim().isEmpty) {
                                        return 'Required';
                                      }
                                      final parsed = int.tryParse(value.trim());
                                      if (parsed == null || parsed < 0) {
                                        return 'Invalid';
                                      }
                                      return null;
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: context.surfaceColor,
                boxShadow: const [
                  BoxShadow(
                    color: Colors.black12,
                    offset: Offset(0, -1),
                    blurRadius: 4,
                  ),
                ],
              ),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isSubmitting ? null : _submitAudit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.forestGreen,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  icon: _isSubmitting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.check_circle_outline_rounded, size: 20),
                  label: Text(
                    _isSubmitting ? 'Submitting...' : 'Submit Audit',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
